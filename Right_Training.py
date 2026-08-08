from ultralytics import YOLO
import os

#Paths
yolo_root = "C:/carla/CARLA0.9.15/yolov5"
data_yaml_path = os.path.join(yolo_root, "vehicles.yaml")
weights_path = os.path.join(yolo_root, "yolov5s.pt")  

# Load model
model = YOLO(weights_path)

# Train the model for right semantic
model.train(
    data=data_yaml_path,  
    epochs=25,
    imgsz=640,
    batch=16,
    name="right_semantic_15ep3",
    project=os.path.join(yolo_root, "runs", "train")
)

