import os
import shutil
from sklearn.model_selection import train_test_split

# Base paths
base_dir = r"C:/carla/CARLA0.9.15/Right Semantic/yolo_dataset"
images_dir = os.path.join(base_dir, "images")
labels_dir = os.path.join(base_dir, "labels")

# Create split folders
for split in ["train", "val"]:
    os.makedirs(os.path.join(images_dir, split), exist_ok=True)
    os.makedirs(os.path.join(labels_dir, split), exist_ok=True)

# Collect all image files
image_files = [f for f in os.listdir(images_dir) if f.endswith((".jpg", ".png"))]
image_basenames = [os.path.splitext(f)[0] for f in image_files]

# Perform train/val split
train_ids, val_ids = train_test_split(image_basenames, test_size=0.2, random_state=42)

def move_files(ids, split):
    for name in ids:
        img_src = os.path.join(images_dir, name + ".png")  # or .jpg if that’s your format
        lbl_src = os.path.join(labels_dir, name + ".txt")

        img_dst = os.path.join(images_dir, split, name + ".png")
        lbl_dst = os.path.join(labels_dir, split, name + ".txt")

        if os.path.exists(img_src):
            shutil.move(img_src, img_dst)
        if os.path.exists(lbl_src):
            shutil.move(lbl_src, lbl_dst)

move_files(train_ids, "train")
move_files(val_ids, "val")

print("✅ Dataset split complete: 'train' and 'val' folders created.")