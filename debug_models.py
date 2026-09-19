import openwakeword
import os
import sys

models_path = os.path.join(os.path.dirname(openwakeword.__file__), 'resources', 'models')
print(f"Checking for models in: {models_path}")

if os.path.exists(models_path):
    print("Files found in models directory:")
    for file in os.listdir(models_path):
        if file.endswith('.onnx'):
            print(f"Found ONNX model: {file}")
else:
    print(f"Model path does NOT exist: {models_path}")
    # Let's try to search the whole site-packages
    site_packages = os.path.dirname(os.path.dirname(openwakeword.__file__))
    print(f"Searching in site-packages: {site_packages}")
    for root, dirs, files in os.walk(site_packages):
        if 'models' in root and any(f.endswith('.onnx') for f in files):
            print(f"Potentially found models at: {root}")
