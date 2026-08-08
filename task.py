# import os
# import sys
# import time
# import cv2
# import math
# import torch
# import random
# import numpy as np
# import carla


# # Path Setup
# carla_root = "C:/carla/CARLA0.9.15"
# yolo_root = os.path.join(carla_root, "yolov5")
# siammask_root = os.path.join(carla_root, "SiamMask")

# sys.path.extend([
#     os.path.join(carla_root, "WindowsNoEditor/PythonAPI"),
#     os.path.join(carla_root, "WindowsNoEditor/PythonAPI/carla"),
#     os.path.join(carla_root, "WindowsNoEditor/PythonAPI/examples"),
#     siammask_root,
#     os.path.join(siammask_root, "experiments/siammask_sharp"),
#     os.path.join(siammask_root, "utils"),
#     os.path.join(siammask_root, "tools"),
#     os.path.join(siammask_root, "models")
# ])

# from SiamMask.experiments.siammask_sharp.custom import Custom as SiamMaskCustom
# from tools.test import siamese_init, siamese_track
# from utils.load_config import load_config
# from utils.load_helper import load_pretrain
# from types import SimpleNamespace

# # Global Constants
# IM_WIDTH, IM_HEIGHT = 1280, 720
# FOV = 105
# actor_list = []
# trackers = {}
# tracker_id_counter = 0
# latest_frame = None

# # YOLOv5 Model (Left Semantic)
# yolo_model_path = os.path.join(yolo_root, "runs/train/exp2/weights/best.pt")
# model_yolo = YOLO(yolo_model_path)

# # SiamMask Model
# siammask_config = os.path.join(siammask_root, "experiments/siammask_sharp/config_VOT18.json")
# siammask_weights = os.path.join(siammask_root, "experiments/siammask_sharp/SiamMask_VOT.pth")

# # SiamMask Wrapper
# torch.set_grad_enabled(False)

# class SiamMask:
#     def __init__(self, config_path, weight_path):
#         self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#         self.cfg = load_config(SimpleNamespace(config=config_path))
#         self.siammask = SiamMaskCustom(anchors=self.cfg['anchors'])
#         self.siammask = load_pretrain(self.siammask, weight_path).eval().to(self.device)
#         self.state = None

#     def initialize_tracker(self, frame, init_bbox):
#         x, y, w, h = init_bbox
#         target_pos = np.array([x + w / 2, y + h / 2])
#         target_sz = np.array([w, h])
#         self.state = siamese_init(frame, target_pos, target_sz, self.siammask, self.cfg['hp'], device=self.device)

#     def track_frame(self, frame):
#         self.state = siamese_track(self.state, frame, mask_enable=True, refine_enable=True, device=self.device)
#         poly = self.state['ploygon'].flatten().reshape((4, 2))
#         x_min, x_max = np.min(poly[:, 0]), np.max(poly[:, 0])
#         y_min, y_max = np.min(poly[:, 1]), np.max(poly[:, 1])
#         return int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)

# # Utility: Classifing Same/Opposite Lane
# def classify_lane_affiliation(world, ego_vehicle, locations):
#     map = world.get_map()
#     ego_wp = map.get_waypoint(ego_vehicle.get_location())
#     result = []
#     for loc in locations:
#         wp = map.get_waypoint(loc)
#         if wp.road_id == ego_wp.road_id:
#             result.append("same_lane" if wp.lane_id == ego_wp.lane_id else "opposite_lane")
#         else:
#             result.append("unknown")
#     return result

# # Main Image Processor
# def process_img(image, world, ego):
#     global trackers, tracker_id_counter, latest_frame
#     image.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(image.raw_data).reshape((IM_HEIGHT, IM_WIDTH, 4))[:, :, :3]
#     i_rgb = np.ascontiguousarray(i)

#     results = model_yolo(i_rgb, verbose=False)
#     detections = []

#     if results and hasattr(results[0], 'boxes'):
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [0, 1, 2]:
#                 detections.append([x1, y1, x2 - x1, y2 - y1])

#     # Assigning new trackers
#     for det in detections:
#         cx, cy = det[0] + det[2] // 2, det[1] + det[3] // 2
#         overlaps = any(abs(cx - (t['bbox'][0] + t['bbox'][2] // 2)) < 50 and
#                        abs(cy - (t['bbox'][1] + t['bbox'][3] // 2)) < 50 for t in trackers.values())
#         if overlaps:
#             continue
#         tracker = SiamMask(siammask_config, siammask_weights)
#         tracker.initialize_tracker(i_rgb, det)
#         trackers[tracker_id_counter] = {'tracker': tracker, 'bbox': det, 'history': []}
#         tracker_id_counter += 1

#     to_remove = []
#     display = i_rgb.copy()
#     for tid, data in trackers.items():
#         try:
#             x, y, w, h = data['tracker'].track_frame(i_rgb)
#         except:
#             to_remove.append(tid)
#             continue

#         trackers[tid]['bbox'] = [x, y, w, h]
#         center = carla.Location(x=float(x + w / 2), y=float(y + h / 2), z=0.0)

#         # Update history
#         data['history'].append((x + w // 2, y + h // 2))
#         if len(data['history']) > 10:
#             data['history'].pop(0)

#         # Estimate Velocity
#         velocity = (0, 0)
#         if len(data['history']) >= 2:
#             dx = data['history'][-1][0] - data['history'][-2][0]
#             dy = data['history'][-1][1] - data['history'][-2][1]
#             velocity = (dx / 0.05, dy / 0.05)

#         # Estimate Distance
#         ego_loc = ego.get_transform().location
#         distance = math.sqrt((center.x - ego_loc.x)**2 + (center.y - ego_loc.y)**2)

#         # Lane classification
#         lane = classify_lane_affiliation(world, ego, [center])[0]

#         # Draw
#         cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
#         cv2.putText(display, f"ID:{tid} V:{int(velocity[0])},{int(velocity[1])} D:{distance:.1f}m {lane}",
#                     (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

#     for tid in to_remove:
#         del trackers[tid]

#     latest_frame = display
#     cv2.imshow("Tracking", display)
#     cv2.waitKey(1)

# # CARLA Setup
# try:
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()

#     spawn_point = world.get_map().get_spawn_points()[1]
#     ego = world.spawn_actor(blueprint_library.filter("vehicle.tesla.model3")[0], spawn_point)
#     actor_list.append(ego)

#     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
#     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
#     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
#     cam_bp.set_attribute("fov", str(FOV))
#     cam_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
#     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
#     actor_list.append(cam)

#     cam.listen(lambda image: process_img(image, world, ego))

#     print("Running Semantic + YOLO + SiamMask + Velocity in CARLA")
#     while True:
#         world.tick()
#         time.sleep(0.05)

# except KeyboardInterrupt:
#     print("Interrupted by user")

# finally:
#     for actor in actor_list:
#         actor.destroy()
#     cv2.destroyAllWindows()



















import os
import sys
import cv2
import time
import torch
import numpy as np
import carla
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# PATH SETUP
carla_root = "C:/carla/CARLA0.9.15"
yolo_root = os.path.join(carla_root, "yolov5")

# YOLOv5 trained model path
model_path = os.path.join(yolo_root, "runs/train/exp2/weights/best.pt")

# Loading YOLOv5 model
model_yolo = YOLO(model_path)

# Initialize DeepSORT
tracker = DeepSort(max_age=30)

# GLOBALS
IM_WIDTH, IM_HEIGHT = 1280, 720
FOV = 105
actor_list = []
latest_frame = None

# Classify same/opposite lane
def classify_lane_affiliation(world, ego_vehicle, targets):
    map = world.get_map()
    ego_wp = map.get_waypoint(ego_vehicle.get_location(), project_to_road=True)
    results = []
    for loc in targets:
        wp = map.get_waypoint(loc, project_to_road=True)
        if wp.road_id == ego_wp.road_id:
            results.append("same_lane" if wp.lane_id == ego_wp.lane_id else "opposite_lane")
        else:
            results.append("unknown")
    return results

# Process Image Callback
def process_img(image, world, ego):
    global latest_frame
    image.convert(carla.ColorConverter.CityScapesPalette)
    img = np.array(image.raw_data).reshape((IM_HEIGHT, IM_WIDTH, 4))[:, :, :3]
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = model_yolo.predict(source=img_rgb, verbose=False)[0]

    detections = []
    for box in results.boxes:
        cls_id = int(box.cls.item())
        if cls_id in [0, 1, 2]:  # car, truck, motorcycle
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf.item())
            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, f"{cls_id}"))

    tracks = tracker.update_tracks(detections, frame=img_rgb)
    display = img.copy()

    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        x1, y1, x2, y2 = map(int, track.to_ltrb())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        carla_loc = carla.Location(x=float(cx), y=float(cy), z=0.0)

        lane = classify_lane_affiliation(world, ego, [carla_loc])[0]
        distance = ego.get_location().distance(carla_loc)

        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(display, f"ID:{track_id} D:{distance:.1f}m {lane}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    latest_frame = display
    cv2.imshow("YOLO + DeepSORT Tracking", display)
    cv2.waitKey(1)

# CARLA Setup
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    spawn_point = world.get_map().get_spawn_points()[1]
    ego = world.spawn_actor(blueprint_library.filter("vehicle.tesla.model3")[0], spawn_point)
    actor_list.append(ego)

    cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
    cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
    cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
    cam_bp.set_attribute("fov", str(FOV))
    cam_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
    cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
    actor_list.append(cam)

    cam.listen(lambda image: process_img(image, world, ego))

    print("YOLOv5 + DeepSORT tracking running. Press Ctrl+C to stop.")
    while True:
        world.tick()
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    for actor in actor_list:
        actor.destroy()
    cv2.destroyAllWindows()
    print("Cleanup complete.")