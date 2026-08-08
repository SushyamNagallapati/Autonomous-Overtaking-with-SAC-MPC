import os
import cv2
import numpy as np
from tqdm import tqdm

# CONFIGURATION
semantic_label_dir = r"C:\carla\CARLA0.9.15\data_2d_semantics\train"
output_image_dir = r"C:\carla\CARLA0.9.15\dataset\images"
output_label_dir = r"C:\carla\CARLA0.9.15\dataset\labels"
os.makedirs(output_image_dir, exist_ok=True)
os.makedirs(output_label_dir, exist_ok=True)

# Vehicle Class Mapping (KITTI ID → YOLO class)
vehicle_classes = {26: 0, 27: 1, 32: 2}

# Process dataset
for seq_folder in tqdm(os.listdir(semantic_label_dir)):
    seq_path = os.path.join(semantic_label_dir, seq_folder)
    rgb_folder = os.path.join(seq_path, "image_00", "semantic_rgb")
    label_folder = os.path.join(seq_path, "image_00", "semantic")

    if not os.path.isdir(rgb_folder) or not os.path.isdir(label_folder):
        continue

    image_files = sorted(os.listdir(rgb_folder))
    label_files = sorted(os.listdir(label_folder))

    for img_file, lbl_file in zip(image_files, label_files):
        img_path = os.path.join(rgb_folder, img_file)
        lbl_path = os.path.join(label_folder, lbl_file)

        image = cv2.imread(img_path)
        label = cv2.imread(lbl_path, cv2.IMREAD_UNCHANGED)

        if image is None or label is None:
            continue  # Skip if file couldn't be read

        h, w = label.shape
        label_txt = []

        for kitti_id, yolo_id in vehicle_classes.items():
            mask = (label == kitti_id).astype(np.uint8) * 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                x_center = (x + bw / 2) / w
                y_center = (y + bh / 2) / h
                norm_w = bw / w
                norm_h = bh / h
                label_txt.append(f"{yolo_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

        out_img_name = f"{seq_folder}_{img_file}"
        cv2.imwrite(os.path.join(output_image_dir, out_img_name), image)
        with open(os.path.join(output_label_dir, out_img_name.replace('.png', '.txt')), 'w') as f:
            f.write("\n".join(label_txt)) 
