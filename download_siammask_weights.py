import os
import urllib.request

# Output directory
base_dir = 'SiamMask/experiments/siammask_sharp'
os.makedirs(base_dir, exist_ok=True)

# ✅ New working links for the pretrained models (Google Drive alternatives)
urls = {
    "SiamMask_DAVIS.pth": "https://github.com/foolwood/SiamMask/releases/download/v0.1/SiamMask_DAVIS.pth",
    "SiamMask_VOT.pth": "https://github.com/foolwood/SiamMask/releases/download/v0.1/SiamMask_VOT.pth"
}

# Download loop
for filename, url in urls.items():
    dest = os.path.join(base_dir, filename)
    print(f"⬇️ Downloading {filename} from {url}")
    urllib.request.urlretrieve(url, dest)
    print(f"✅ Saved: {dest}")
