import os
import gdown

# Folder where weights will be saved
base_dir = 'SiamMask/experiments/siammask_sharp'
os.makedirs(base_dir, exist_ok=True)

# File ID from Google Drive (shared public links)
files = {
    "SiamMask_DAVIS.pth": "1S4uCIbQH_jpF5P3_wYjWqL93hz3D71Et",
    "SiamMask_VOT.pth": "1cYbD3UebLL3Aj2Um2fDoUgz3_Ee8t2hD"
}

# Download files
for filename, file_id in files.items():
    dest = os.path.join(base_dir, filename)
    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"⬇️ Downloading {filename} from Google Drive...")
    gdown.download(url, dest, quiet=False)
    print(f"✅ Saved: {dest}")
