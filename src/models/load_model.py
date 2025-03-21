import os
import sys
import shutil
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def load_external_model(model_path):
    """
    Load an external model file (.pkl) and save it to the trained models directory
    
    Args:
        model_path (str): Path to the external model file
    """
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the trained models directory
    trained_dir = os.path.join(current_dir, "trained")
    
    # Create the directory if it doesn't exist
    os.makedirs(trained_dir, exist_ok=True)
    
    # Target path for the model
    target_path = os.path.join(trained_dir, "fraud_model.pkl")
    
    try:
        # Check if the file is a valid model
        model_data = joblib.load(model_path)
        
        # Verify model structure
        if isinstance(model_data, dict):
            if "model" not in model_data or "scaler" not in model_data:
                # Create a compatible structure
                if isinstance(model_data, dict):
                    # Try to adapt the existing structure
                    new_model_data = {}
                    
                    # Look for model and scaler in the dictionary
                    for key, value in model_data.items():
                        if isinstance(value, RandomForestClassifier) or "RandomForest" in str(type(value)):
                            new_model_data["model"] = value
                        elif isinstance(value, StandardScaler) or "Scaler" in str(type(value)):
                            new_model_data["scaler"] = value
                    
                    # If we couldn't find a model or scaler, create defaults
                    if "model" not in new_model_data:
                        print("Warning: Could not find a RandomForestClassifier in the model file. Using a default model.")
                        new_model_data["model"] = RandomForestClassifier(n_estimators=100, random_state=42)
                    
                    if "scaler" not in new_model_data:
                        print("Warning: Could not find a StandardScaler in the model file. Using a default scaler.")
                        new_model_data["scaler"] = StandardScaler()
                    
                    # Save the adapted model
                    joblib.dump(new_model_data, target_path)
                    print(f"Model adapted and saved to {target_path}")
                else:
                    # If it's a single model without a scaler
                    if isinstance(model_data, RandomForestClassifier) or "RandomForest" in str(type(model_data)):
                        new_model_data = {
                            "model": model_data,
                            "scaler": StandardScaler()
                        }
                        joblib.dump(new_model_data, target_path)
                        print(f"Model adapted and saved to {target_path}")
                    else:
                        print("Error: The model file does not contain a compatible model structure.")
                        return False
            else:
                # The model has the correct structure, just copy it
                shutil.copy(model_path, target_path)
                print(f"Model copied to {target_path}")
        else:
            # Try to adapt the model
            if isinstance(model_data, RandomForestClassifier) or "RandomForest" in str(type(model_data)):
                new_model_data = {
                    "model": model_data,
                    "scaler": StandardScaler()
                }
                joblib.dump(new_model_data, target_path)
                print(f"Model adapted and saved to {target_path}")
            else:
                print("Error: The model file does not contain a compatible model structure.")
                return False
        
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python load_model.py <path_to_model.pkl>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    if not os.path.exists(model_path):
        print(f"Error: Model file {model_path} does not exist.")
        sys.exit(1)
    
    success = load_external_model(model_path)
    if success:
        print("Model loaded successfully!")
    else:
        print("Failed to load model.")
        sys.exit(1)
