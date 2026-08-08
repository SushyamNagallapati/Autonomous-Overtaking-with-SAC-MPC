from ultralytics import YOLO
import os

# === Paths ===
yolo_root = "C:/carla/CARLA0.9.15/yolov5"
data_yaml_path = os.path.join(yolo_root, "vehicles_left.yaml")
best_weights = os.path.join(yolo_root, "runs/train/exp2/weights/best.pt")  # Previous left semantic model

# === Load YOLOv5 model from best.pt ===
model = YOLO(best_weights)

# === Fine-tune training ===
model.train(
    data=data_yaml_path,
    epochs=30,
    imgsz=640,
    batch=16,
    name="exp2_left_ft",  # Fine-tuned left dataset
    project=os.path.join(yolo_root, "runs", "train")
)

# Output: C:/carla/CARLA0.9.15/yolov5/runs/train/exp2_left_ft/weights
