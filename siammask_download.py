import os
import urllib.request
import zipfile

print("📦 Downloading SiamMask repository...")

# Download the ZIP
url = "https://github.com/foolwood/SiamMask/archive/refs/heads/master.zip"
output_zip = "siammask_master.zip"

urllib.request.urlretrieve(url, output_zip)
print("✅ SiamMask ZIP downloaded.")

# Extract to current directory
with zipfile.ZipFile(output_zip, 'r') as zip_ref:
    zip_ref.extractall(".")

# Move extracted folder to replace your existing one safely
if not os.path.exists("SiamMask"):
    os.rename("SiamMask-master", "SiamMask")

# Clean up
os.remove(output_zip)
print("✅ SiamMask setup completed.")
