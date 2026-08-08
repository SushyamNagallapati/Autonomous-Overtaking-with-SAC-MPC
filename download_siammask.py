# === Step 1: SiamMask Setup ===
# This code downloads and sets up the SiamMask model if not already present

import os
import zipfile
import urllib.request

# Define paths
siammask_repo_url = "https://github.com/foolwood/SiamMask/archive/refs/heads/master.zip"
siammask_local_dir = "siammask"
siammask_model_url = "https://www.robots.ox.ac.uk/~qwang/SiamMask_VOT.pth"
siammask_model_path = os.path.join(siammask_local_dir, "SiamMask_VOT.pth")

# Create folder if it doesn't exist
if not os.path.exists(siammask_local_dir):
    print("📦 Downloading SiamMask repository...")
    urllib.request.urlretrieve(siammask_repo_url, "siammask.zip")
    with zipfile.ZipFile("siammask.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
    os.rename("SiamMask-master", siammask_local_dir)
    os.remove("siammask.zip")
    print("✅ SiamMask repository downloaded and extracted.")

# Download pre-trained model if missing
if not os.path.exists(siammask_model_path):
    print("📥 Downloading SiamMask pre-trained model...")
    urllib.request.urlretrieve(siammask_model_url, siammask_model_path)
    print("✅ SiamMask model downloaded.")
else:
    print("✅ SiamMask pre-trained model already available.")