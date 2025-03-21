import os
import sys
import subprocess

# Determine which app to run based on WEBSITE_SITE_NAME environment variable
site_name = os.environ.get('WEBSITE_SITE_NAME', '').lower()

# Set environment variables
os.environ['PYTHONUNBUFFERED'] = '1'

# Determine port from environment or use default
port = os.environ.get('PORT', '8000')

if 'api' in site_name:
    # Start the API
    print("Starting API server...")
    os.chdir(os.path.join(os.path.dirname(__file__), 'src', 'api'))
    from src.api.main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(port))
elif 'dashboard' in site_name:
    # Start the Dashboard
    print("Starting Dashboard...")
    os.chdir(os.path.join(os.path.dirname(__file__), 'src', 'dashboard'))
    from src.dashboard.app import server
    server.run(host="0.0.0.0", port=int(port))
else:
    # Default to API if not specified
    print(f"Unknown site name: {site_name}. Defaulting to API server...")
    os.chdir(os.path.join(os.path.dirname(__file__), 'src', 'api'))
    from src.api.main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(port))
