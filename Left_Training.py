from ultralytics import YOLO
import os

# === Paths ===
yolo_root = "C:/carla/CARLA0.9.15/yolov5"
data_yaml_path = os.path.join(yolo_root, "vehicles.yaml")
weights_path = os.path.join(yolo_root, "yolov5s.pt")

# Load model
model = YOLO(weights_path)

# Training the model
model.train(
    data=data_yaml_path,   # path to dataset config
    epochs=50,
    imgsz=640,
    batch=16,
    name="exp2",
    project=os.path.join(yolo_root, "runs", "train")
)

