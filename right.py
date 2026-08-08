import os
import cv2
import numpy as np
from tqdm import tqdm

# ID to YOLO class mapping (update if needed)
valid_ids = {
    30: 0,  # Car
    31: 1,  # Truck
    32: 2   # Motorcycle
}

input_root = r"C:\carla\CARLA0.9.15\Right Semantic\data_2d_semantics\train"
output_images = r"C:\carla\CARLA0.9.15\Right Semantic\yolo_dataset\images"
output_labels = r"C:\carla\CARLA0.9.15\Right Semantic\yolo_dataset\labels"

os.makedirs(output_images, exist_ok=True)
os.makedirs(output_labels, exist_ok=True)

# Helper function to convert bounding box
def mask_to_bbox(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        boxes.append([x, y, x + w, y + h])
    return boxes

for sequence in os.listdir(input_root):
    semantic_path = os.path.join(input_root, sequence, "image_01", "semantic")
    image_path = os.path.join(input_root, sequence, "image_01", "data")

    if not os.path.isdir(semantic_path):
        continue

    for fname in tqdm(os.listdir(semantic_path), desc=f"Processing {sequence}"):
        if not fname.endswith(".png"):
            continue

        sem_img = cv2.imread(os.path.join(semantic_path, fname), cv2.IMREAD_UNCHANGED)
        if sem_img is None:
            continue

        height, width = sem_img.shape
        label_lines = []

        for sem_id, class_id in valid_ids.items():
            mask = (sem_img == sem_id).astype(np.uint8) * 255
            boxes = mask_to_bbox(mask)

            for box in boxes:
                x1, y1, x2, y2 = box
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height
                label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        # Write YOLO label file
        outname = fname.replace(".png", ".txt")
        with open(os.path.join(output_labels, outname), "w") as f:
            f.write("\n".join(label_lines))

        # Copy image
        src_img = os.path.join(image_path, fname)
        if os.path.exists(src_img):
            cv2.imwrite(os.path.join(output_images, fname), cv2.imread(src_img))

print("YOLO conversion complete.")