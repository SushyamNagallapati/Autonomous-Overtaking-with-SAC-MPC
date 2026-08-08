import os
import shutil

semantic_root = r"C:/carla/CARLA0.9.15/Right Semantic/data_2d_semantics/train"
output_dir = r"C:/carla/CARLA0.9.15/Right Semantic/yolo_dataset/images"
os.makedirs(output_dir, exist_ok=True)

count = 0

for root, _, files in os.walk(semantic_root):
    for file in files:
        if file.endswith(".png"):
            src = os.path.join(root, file)
            dst = os.path.join(output_dir, file)      
            if not os.path.exists(dst):
                shutil.copy(src, dst)
                count += 1

print(f"✅ Moved {count} .png files to {output_dir}")