import os

# Define base path and create it if not exist
base_path = "C:/carla/CARLA0.9.15/Right Semantic/yolo_dataset"
os.makedirs(base_path, exist_ok=True)

# Convert backslashes to forward slashes for YOLO YAML
train_path = base_path.replace("\\", "/") + "/images/train"
val_path = base_path.replace("\\", "/") + "/images/val"

# Create YAML file
yaml_path = os.path.join(base_path, "data.yaml")
with open(yaml_path, "w") as f:
    f.write(f"""train: {train_path}
val: {val_path}

nc: 3
names: ['car', 'truck', 'motorcycle']
""")

print(f"data.yaml created at: {yaml_path}")
