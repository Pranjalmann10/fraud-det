# Azure Deployment Guide

This guide provides instructions for deploying the Fraud Detection, Alert, and Monitoring (FDAM) System to Azure using GitHub Actions.

## Prerequisites

1. An Azure account with active subscription
2. A GitHub account with your code repository
3. Azure CLI installed (optional, for local configuration)

## Setup Azure Resources

### 1. Create Azure App Services

Create two Azure App Services, one for the API and one for the Dashboard:

```bash
# Login to Azure
az login

# Create a resource group
az group create --name fdam-resources --location eastus

# Create App Service Plans
az appservice plan create --name fdam-plan --resource-group fdam-resources --sku B1 --is-linux

# Create Web Apps
az webapp create --name fdam-api --resource-group fdam-resources --plan fdam-plan --runtime "PYTHON:3.10"
az webapp create --name fdam-dashboard --resource-group fdam-resources --plan fdam-plan --runtime "PYTHON:3.10"
```

### 2. Set up Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres server create --name fdam-postgres --resource-group fdam-resources --location eastus --admin-user dbadmin --admin-password <your-password> --sku-name GP_Gen5_2

# Create database
az postgres db create --name fraud_detection --server-name fdam-postgres --resource-group fdam-resources

# Configure firewall rules
az postgres server firewall-rule create --name AllowAllAzureIPs --server-name fdam-postgres --resource-group fdam-resources --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

### 3. Create Azure Key Vault for Secrets

```bash
# Create Key Vault
az keyvault create --name fdam-kv --resource-group fdam-resources --location eastus

# Add database connection string as secret
az keyvault secret set --vault-name fdam-kv --name DATABASE-URL --value "postgresql://dbadmin:<your-password>@fdam-postgres.postgres.database.azure.com:5432/fraud_detection?sslmode=require"

# Grant access to App Services
az webapp identity assign --name fdam-api --resource-group fdam-resources
API_PRINCIPAL_ID=$(az webapp identity show --name fdam-api --resource-group fdam-resources --query principalId --output tsv)

az webapp identity assign --name fdam-dashboard --resource-group fdam-resources
DASHBOARD_PRINCIPAL_ID=$(az webapp identity show --name fdam-dashboard --resource-group fdam-resources --query principalId --output tsv)

az keyvault set-policy --name fdam-kv --resource-group fdam-resources --object-id $API_PRINCIPAL_ID --secret-permissions get list
az keyvault set-policy --name fdam-kv --resource-group fdam-resources --object-id $DASHBOARD_PRINCIPAL_ID --secret-permissions get list
```

## Configure GitHub Actions

### 1. Add GitHub Secrets

In your GitHub repository, go to Settings > Secrets and add the following secrets:

1. `AZURE_CREDENTIALS`: Service principal credentials
   
   Generate using:
   
   ```bash
   az ad sp create-for-rbac --name "fdam-github-actions" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/fdam-resources --sdk-auth
   ```
   
   Copy the entire JSON output as the secret value.

2. `AZURE_API_PUBLISH_PROFILE`: Publish profile for the API app
   
   Generate using:
   
   ```bash
   az webapp deployment list-publishing-profiles --name fdam-api --resource-group fdam-resources --xml
   ```
   
   Copy the entire XML output as the secret value.

3. `AZURE_DASHBOARD_PUBLISH_PROFILE`: Publish profile for the dashboard app
   
   Generate using:
   
   ```bash
   az webapp deployment list-publishing-profiles --name fdam-dashboard --resource-group fdam-resources --xml
   ```
   
   Copy the entire XML output as the secret value.

### 2. Configure App Settings

Set up environment variables for each App Service:

```bash
# API App Settings
az webapp config appsettings set --name fdam-api --resource-group fdam-resources --settings \
  DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://fdam-kv.vault.azure.net/secrets/DATABASE-URL/)" \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  WEBSITE_MOUNT_ENABLED=1 \
  HOST=0.0.0.0 \
  PORT=8001

# Dashboard App Settings
az webapp config appsettings set --name fdam-dashboard --resource-group fdam-resources --settings \
  API_BASE_URL="https://fdam-api.azurewebsites.net/api" \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  WEBSITE_MOUNT_ENABLED=1 \
  DEBUG=false \
  HOST=0.0.0.0 \
  PORT=8050
```

## Deploy with GitHub Actions

Once you've set up all the necessary Azure resources and GitHub secrets, push your code to the main branch or manually trigger the GitHub Actions workflow to deploy the application.

### 1. Verify Deployment

After deployment, you can access your applications at:
- API: https://fdam-api.azurewebsites.net
- Dashboard: https://fdam-dashboard.azurewebsites.net

### 2. Monitor Applications

Use Azure Monitor to track the health and performance of your applications:

```bash
# View application logs
az webapp log tail --name fdam-api --resource-group fdam-resources
az webapp log tail --name fdam-dashboard --resource-group fdam-resources
```

## Troubleshooting

1. **Deployment Failures**:
   - Check GitHub Actions logs
   - Ensure all GitHub secrets are correctly configured
   - Verify that the App Service configurations are correct

2. **Database Connection Issues**:
   - Verify that the connection string is correct
   - Check that the Azure Key Vault access policies are properly set
   - Ensure that firewall rules allow connections

3. **Application Errors**:
   - Check application logs using Azure Portal or Azure CLI
   - Verify environment variables are set correctly

## Additional Resources

- [Azure Web Apps Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [GitHub Actions for Azure](https://github.com/marketplace/actions/azure-login)
- [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)
