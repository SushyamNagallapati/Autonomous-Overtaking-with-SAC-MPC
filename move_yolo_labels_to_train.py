# import os
# import shutil

# # Base directory
# base = r"C:/carla/CARLA0.9.15/Right Semantic/yolo_dataset"

# labels_dir = os.path.join(base, "labels")
# train_dir = os.path.join(labels_dir, "train")

# # Create train directory if not exists
# os.makedirs(train_dir, exist_ok=True)

# # Move all .txt files into labels/train
# for file in os.listdir(labels_dir):
#     if file.endswith(".txt"):
#         src = os.path.join(labels_dir, file)
#         dst = os.path.join(train_dir, file)
#         shutil.move(src, dst)

# print("✅ All label files moved to 'labels/train'")






# import os

# label_dir = r'C:\carla\CARLA0.9.15\Right Semantic\yolo_dataset\labels\train'

# empty_files = []
# for file in os.listdir(label_dir):
#     path = os.path.join(label_dir, file)
#     if os.path.isfile(path) and os.path.getsize(path) == 0:
#         empty_files.append(file)

# print(f"🔍 Found {len(empty_files)} empty label files out of {len(os.listdir(label_dir))}")
# if empty_files:
#     print("Example empty files:", empty_files[:5])










import os
import shutil

# Root of your YOLO dataset
base_dir = "C:/carla/CARLA0.9.15/Right Semantic/yolo_dataset/labels"
train_dir = os.path.join(base_dir, "train")

# Create train directory if it doesn't exist
os.makedirs(train_dir, exist_ok=True)

moved = 0
for root, dirs, files in os.walk(base_dir):
    # Skip 'train' and 'val' folders to avoid infinite loop
    if "train" in root or "val" in root:
        continue

    for file in files:
        if file.endswith(".txt"):
            src = os.path.join(root, file)
            dst = os.path.join(train_dir, file)

            if not os.path.exists(dst):
                shutil.move(src, dst)
                moved += 1

print(f"✅ Moved {moved} label files to 'labels/train'")