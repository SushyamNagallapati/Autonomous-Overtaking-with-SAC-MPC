# # === Enhanced CARLA + YOLOv5 + SiamMask Integration ===
# # Includes YOLOv5 detection, SiamMask tracking, semantic cam

# import os
# import sys
# import time
# import cv2
# import numpy as np
# import random
# import math
# import torch

# import carla
# from ultralytics import YOLO

# # PATH SETUP
# carla_root = "C:/carla/CARLA0.9.15"
# siammask_root = "C:/carla/CARLA0.9.15/SiamMask"
# sys.path.append(siammask_root)
# sys.path.append(os.path.join(siammask_root, "experiments", "siammask_sharp"))
# sys.path.append(os.path.join(siammask_root, "utils"))
# sys.path.append(os.path.join(siammask_root, "tools"))
# sys.path.append(os.path.join(siammask_root, "models"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))

# from agents.navigation.global_route_planner import GlobalRoutePlanner
# from agents.tools.misc import distance_vehicle

# from SiamMask.experiments.siammask_sharp.custom import Custom as SiamMaskCustom
# from tools.test import siamese_init, siamese_track
# from utils.load_config import load_config
# from types import SimpleNamespace

# # SiamMask Wrapper
# torch.set_grad_enabled(False)

# class SiamMask:
#     def __init__(self, config_path, weight_path, device='cuda'):
#         self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if device is None else device
#         self.cfg = load_config(SimpleNamespace(config=config_path))
#         self.siammask = SiamMaskCustom(anchors=self.cfg['anchors'])
#         self.siammask = load_pretrain(self.siammask, weight_path)
#         self.siammask = self.siammask.eval().to(self.device)
#         self.state = None

#     def initialize_tracker(self, frame, init_bbox):
#         x, y, w, h = init_bbox
#         target_pos = np.array([x + w / 2, y + h / 2])
#         target_sz = np.array([w, h])
#         self.state = siamese_init(frame, target_pos, target_sz, self.siammask, self.cfg['hp'], device=self.device)

#     def track_frame(self, frame):
#         if self.state is None:
#             raise ValueError("Tracker not initialized")
#         self.state = siamese_track(self.state, frame, mask_enable=True, refine_enable=True, device=self.device)
#         polygon = self.state['ploygon'].flatten().reshape((4, 2))
#         x_coords = polygon[:, 0]
#         y_coords = polygon[:, 1]
#         x_min, x_max = np.min(x_coords), np.max(x_coords)
#         y_min, y_max = np.min(y_coords), np.max(y_coords)
#         return int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)

# # GLOBALS
# IM_WIDTH, IM_HEIGHT, IM_CHANNEL = 1280, 720, 4
# FOV = 105
# actor_list = []
# model_yolo = YOLO("yolov5su.pt")
# tracker_id_counter = 0
# trackers = {}  # {id: {'tracker': SiamMask, 'bbox': last_bbox}}

# siammask_config = os.path.join(siammask_root, "experiments", "siammask_sharp", "config_VOT18.json")
# siammask_weights = os.path.join(siammask_root, "experiments", "siammask_sharp", "SiamMask_VOT.pth")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('yolo_siammask_output.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))
# latest_frame = None

# # IMAGE PROCESSING
# def process_img(frame):
#     global latest_frame, tracker_id_counter, trackers

#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i_rgb = np.ascontiguousarray(i, dtype=np.uint8)
#     display = i_rgb.copy()
#     gray = cv2.cvtColor(i_rgb, cv2.COLOR_BGR2GRAY)

#     # Keep previous gray frame for optical flow
#     if not hasattr(process_img, "prev_gray"):
#         process_img.prev_gray = gray.copy()
#         process_img.prev_bbox_flow = {}  # {tracker_id: (x, y) motion vector}

#     results = model_yolo(i_rgb, verbose=False)
#     new_detections = []

#     if results and hasattr(results[0], 'boxes'):
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 bbox = [x1, y1, x2 - x1, y2 - y1]
#                 center = (x1 + x2) // 2, (y1 + y2) // 2
#                 duplicate = False
#                 for track in trackers.values():
#                     tx, ty, tw, th = map(int, track['bbox'])
#                     if abs(center[0] - (tx + tw // 2)) < 50 and abs(center[1] - (ty + th // 2)) < 50:
#                         duplicate = True
#                         break
#                 if not duplicate:
#                     new_detections.append(bbox)

#     for bbox in new_detections:
#         tracker = SiamMask(siammask_config, siammask_weights)
#         tracker.initialize_tracker(i_rgb, bbox)
#         trackers[tracker_id_counter] = {'tracker': tracker, 'bbox': bbox}
#         tracker_id_counter += 1

#     to_remove = []
#     for tid, data in trackers.items():
#         try:
#             x, y, w, h = data['tracker'].track_frame(i_rgb)
#         except:
#             to_remove.append(tid)
#             continue

#         if x < 0 or y < 0 or x + w > IM_WIDTH or y + h > IM_HEIGHT:
#             to_remove.append(tid)
#             continue

#         trackers[tid]['bbox'] = [x, y, w, h]

#         # Optical Flow in Bounding Box
#         curr_gray = gray
#         prev_gray = process_img.prev_gray
#         prev_roi = prev_gray[y:y+h, x:x+w]
#         curr_roi = curr_gray[y:y+h, x:x+w]
#         if prev_roi.shape == curr_roi.shape and prev_roi.size > 0:
#             flow = cv2.calcOpticalFlowFarneback(prev_roi, curr_roi, None,
#                                                 pyr_scale=0.5, levels=3, winsize=15,
#                                                 iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
#             dx = np.mean(flow[..., 0])
#             dy = np.mean(flow[..., 1])
#             velocity = math.sqrt(dx**2 + dy**2)
#             cv2.putText(display, f"V: {velocity:.2f}px", (x, y + h + 15),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

#         # Draw tracking box
#         cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
#         cv2.putText(display, f"ID {tid}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

#     for tid in to_remove:
#         del trackers[tid]

#     process_img.prev_gray = gray.copy()
#     latest_frame = display
#     out.write(display)
#     return display / 255.0

# # SPAWN TRAFFIC
# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for _ in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list

# try:
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()

#     blueprint_library = world.get_blueprint_library()
#     vehicle_bp = blueprint_library.filter("mkz_2020")[0]
#     spawn_point = world.get_map().get_spawn_points()[1]
#     ego = world.spawn_actor(vehicle_bp, spawn_point)
#     actor_list.append(ego)

#     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
#     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
#     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
#     cam_bp.set_attribute("fov", str(FOV))
#     cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
#     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
#     actor_list.append(cam)
#     cam.listen(lambda data: process_img(data))

#     env_map = world.get_map()
#     route_planner = GlobalRoutePlanner(env_map, 2.0)
#     point_a = carla.Location(x=299.4, y=129.75, z=0.29)
#     point_b = carla.Location(x=-2.02, y=209.42, z=-0.01)
#     route = route_planner.trace_route(point_a, point_b)

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(
#         spawn_point.location + carla.Location(x=-6, z=2),
#         carla.Rotation(yaw=spawn_point.rotation.yaw)))

#     def show_loop():
#         while True:
#             if latest_frame is not None:
#                 cv2.imshow("YOLO + SiamMask Tracking", latest_frame)
#                 key = cv2.waitKey(1)
#                 if key == ord('q'):
#                     break

#     import threading
#     t = threading.Thread(target=show_loop, daemon=True)
#     t.start()

#     def follow_route(vehicle, route):
#         for i in range(len(route)):
#             if i + 5 < len(route):
#                 target_waypoint = route[i + 5][0].transform.location
#             else:
#                 target_waypoint = route[-1][0].transform.location

#             while True:
#                 location = vehicle.get_transform().location
#                 direction = target_waypoint - location
#                 distance = math.sqrt(direction.x**2 + direction.y**2)
#                 if distance < 2.0:
#                     break
#                 angle = math.atan2(direction.y, direction.x)
#                 yaw = math.radians(vehicle.get_transform().rotation.yaw)
#                 yaw_diff = (angle - yaw + math.pi) % (2 * math.pi) - math.pi
#                 steer = max(-1.0, min(1.0, yaw_diff * 2.0))
#                 throttle = min(0.6, distance * 0.15)
#                 vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer))
#                 time.sleep(0.05)
#         print("Route completed!")

#     follow_route(ego, route)
#     time.sleep(2)

# finally:
#     print("Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("Cleanup complete.")







































import os
import sys
import time
import cv2
import numpy as np
import math
import torch
import random
import carla
from ultralytics import YOLO

# === Paths ===
carla_root = "C:/carla/CARLA0.9.15"
yolo_root = os.path.join(carla_root, "yolov5")
siammask_root = os.path.join(carla_root, "SiamMask")

# YOLOv5 left semantic model path
best_weights = os.path.join(yolo_root, "runs/train/exp2/weights/best.pt")

# Append all paths
sys.path.extend([
    os.path.join(carla_root, "WindowsNoEditor/PythonAPI"),
    os.path.join(carla_root, "WindowsNoEditor/PythonAPI/carla"),
    os.path.join(carla_root, "WindowsNoEditor/PythonAPI/examples"),
    siammask_root,
    os.path.join(siammask_root, "experiments/siammask_sharp"),
    os.path.join(siammask_root, "utils"),
    os.path.join(siammask_root, "tools"),
    os.path.join(siammask_root, "models")
])

from agents.navigation.global_route_planner import GlobalRoutePlanner
from agents.tools.misc import distance_vehicle
from SiamMask.experiments.siammask_sharp.custom import Custom as SiamMaskCustom
from tools.test import siamese_init, siamese_track
from utils.load_config import load_config
from utils.load_helper import load_pretrain
from types import SimpleNamespace

# === SiamMask Wrapper ===
torch.set_grad_enabled(False)

class SiamMask:
    def __init__(self, config_path, weight_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.cfg = load_config(SimpleNamespace(config=config_path))
        self.siammask = SiamMaskCustom(anchors=self.cfg['anchors'])
        self.siammask = load_pretrain(self.siammask, weight_path).eval().to(self.device)
        self.state = None

    def initialize_tracker(self, frame, init_bbox):
        x, y, w, h = init_bbox
        target_pos = np.array([x + w / 2, y + h / 2])
        target_sz = np.array([w, h])
        self.state = siamese_init(frame, target_pos, target_sz, self.siammask, self.cfg['hp'], device=self.device)

    def track_frame(self, frame):
        if self.state is None:
            raise ValueError("Tracker not initialized")
        self.state = siamese_track(self.state, frame, mask_enable=True, refine_enable=True, device=self.device)
        poly = self.state['ploygon'].flatten().reshape((4, 2))
        x_min, x_max = np.min(poly[:, 0]), np.max(poly[:, 0])
        y_min, y_max = np.min(poly[:, 1]), np.max(poly[:, 1])
        return int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)

# === Constants and Globals ===
IM_WIDTH, IM_HEIGHT = 1280, 720
model_yolo = YOLO(best_weights)  # Load left semantic-trained model
trackers = {}
actor_list = []
siammask_config = os.path.join(siammask_root, "experiments/siammask_sharp/config_VOT18.json")
siammask_weights = os.path.join(siammask_root, "experiments/siammask_sharp/SiamMask_VOT.pth")
tracker_id_counter = 0
latest_frame = None

def process_img(image, world, ego_vehicle):
    global trackers, tracker_id_counter, latest_frame
    image.convert(carla.ColorConverter.CityScapesPalette)
    i = np.array(image.raw_data, dtype=np.uint8).reshape((IM_HEIGHT, IM_WIDTH, 4))[:, :, :3]
    i_rgb = np.ascontiguousarray(i, dtype=np.uint8)
    display = i_rgb.copy()

    results = model_yolo(i_rgb, verbose=False)
    detections = []

    if results and hasattr(results[0], 'boxes'):
        for box in results[0].boxes.data.tolist():
            x1, y1, x2, y2, conf, cls = map(int, box[:6])
            if cls in [0, 1, 2]:
                detections.append([x1, y1, x2 - x1, y2 - y1])

    for det in detections:
        cx, cy = det[0] + det[2] // 2, det[1] + det[3] // 2
        if any(abs(cx - (t['bbox'][0] + t['bbox'][2] // 2)) < 50 and abs(cy - (t['bbox'][1] + t['bbox'][3] // 2)) < 50 for t in trackers.values()):
            continue
        tracker = SiamMask(siammask_config, siammask_weights)
        tracker.initialize_tracker(i_rgb, det)
        trackers[tracker_id_counter] = {'tracker': tracker, 'bbox': det}
        tracker_id_counter += 1

    to_remove = []
    for tid, tdata in trackers.items():
        try:
            x, y, w, h = tdata['tracker'].track_frame(i_rgb)
        except:
            to_remove.append(tid)
            continue

        trackers[tid]['bbox'] = [x, y, w, h]
        center = carla.Location(x=float(x + w // 2), y=float(y + h // 2), z=0.0)
        lane_type = classify_lane_affiliation(world, ego_vehicle, [center])[0]

        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(display, f"ID:{tid} - {lane_type}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    for tid in to_remove:
        del trackers[tid]

    latest_frame = display
    cv2.imshow("Tracking", display)
    cv2.waitKey(1)

# === Lane Classification ===
def classify_lane_affiliation(world, ego_vehicle, locations):
    map = world.get_map()
    ego_wp = map.get_waypoint(ego_vehicle.get_location())
    results = []
    for loc in locations:
        wp = map.get_waypoint(loc)
        if wp.road_id == ego_wp.road_id:
            if wp.lane_id == ego_wp.lane_id:
                results.append("same_lane")
            else:
                results.append("opposite_lane")
        else:
            results.append("unknown")
    return results

# === Setup CARLA ===
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()

    spawn_point = world.get_map().get_spawn_points()[1]
    ego = world.spawn_actor(bp_lib.filter("vehicle.tesla.model3")[0], spawn_point)
    actor_list.append(ego)

    cam_bp = bp_lib.find("sensor.camera.semantic_segmentation")
    cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
    cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
    cam_bp.set_attribute("fov", "105")
    cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
    cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
    actor_list.append(cam)

    cam.listen(lambda data: process_img(data, world, ego))

    print("Running left semantic YOLO + SiamMask tracking... Press Ctrl+C to exit.")
    while True:
        world.tick()
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopped.")

finally:
    print("Cleaning up...")
    for actor in actor_list:
        if actor:
            actor.destroy()
    cv2.destroyAllWindows()
