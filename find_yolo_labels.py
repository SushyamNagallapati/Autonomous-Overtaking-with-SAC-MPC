import os

root_dir = r"C:\carla\CARLA0.9.15\Right Semantic\yolo_dataset"

txt_files = []
for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".txt"):
            txt_files.append(os.path.join(root, file))

print(f"Found {len(txt_files)} YOLO label files:")
for f in txt_files[:10]:
    print(" -", f)