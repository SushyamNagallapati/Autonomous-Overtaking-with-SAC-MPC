# # === Enhanced CARLA + YOLOv5 + SiamMask Integration ===
# # Includes YOLOv5 detection, SiamMask tracking, semantic cam

# import glob
# import os
# import sys
# import time
# import cv2
# import numpy as np
# import random
# import math
# import torch
# from collections import defaultdict

# import carla
# from ultralytics import YOLO

# # === PATH SETUP ===
# carla_root = "C:/carla/CARLA0.9.15"
# siammask_root = "C:/carla/CARLA0.9.15/SiamMask"  # Update if different
# sys.path += [
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"),
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"),
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"),
#     os.path.join(siammask_root)
# ]

# from agents.navigation.global_route_planner import GlobalRoutePlanner
# from agents.tools.misc import distance_vehicle

# # === SiamMask Setup ===
# from siam_mask.custom import Custom
# from tools.test import siamese_init, siamese_track
# import yaml

# # === GLOBALS ===
# IM_WIDTH, IM_HEIGHT, IM_CHANNEL = 1280, 720, 4
# FOV = 105
# actor_list = []
# model_yolo = YOLO("yolov5su.pt")
# tracker_id_counter = 0
# trackers = dict()  # {id: {tracker, last_bbox}}
# detected_ids = set()

# # Load SiamMask model
# cfg_path = os.path.join(siammask_root, "experiments", "siammask_sharp", "config.yaml")
# with open(cfg_path, 'r') as f:
#     cfg = yaml.safe_load(f)
# siammask = Custom(anchors=cfg['anchors'])
# siammask.load_weights(os.path.join(siammask_root, "SiamMask_DAVIS.pth"))
# siammask.eval().cuda()

# # === Output Video ===
# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('yolo_siammask_output.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))
# latest_frame = None

# # === IMAGE PROCESSING ===
# def process_img(frame):
#     global latest_frame, tracker_id_counter, trackers

#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i_rgb = np.ascontiguousarray(i, dtype=np.uint8)
#     display = i_rgb.copy()

#     # === YOLO DETECTION ===
#     results = model_yolo(i_rgb, verbose=False)
#     new_detections = []

#     if results and hasattr(results[0], 'boxes'):
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:  # vehicle classes
#                 bbox = [x1, y1, x2 - x1, y2 - y1]
#                 center = (x1 + x2) // 2, (y1 + y2) // 2
#                 duplicate = False
#                 for track in trackers.values():
#                     tx, ty, tw, th = map(int, track['last_bbox'])
#                     if abs(center[0] - (tx + tw // 2)) < 50 and abs(center[1] - (ty + th // 2)) < 50:
#                         duplicate = True
#                         break
#                 if not duplicate:
#                     new_detections.append(bbox)

#     # === INITIATE NEW TRACKS ===
#     for bbox in new_detections:
#         x, y, w, h = map(int, bbox)
#         target_pos = np.array([x + w / 2, y + h / 2])
#         target_sz = np.array([w, h])
#         state = siamese_init(i_rgb, target_pos, target_sz, siammask)
#         trackers[tracker_id_counter] = {'state': state, 'last_bbox': bbox}
#         tracker_id_counter += 1

#     # === TRACK EXISTING ===
#     to_remove = []
#     for tid, track in trackers.items():
#         state = track['state']
#         state = siamese_track(state, i_rgb, mask_enable=True, refine_enable=True)
#         track['state'] = state
#         bbox = state['target_pos'] - state['target_sz'] / 2
#         bbox = np.concatenate([bbox, state['target_sz']])
#         x, y, w, h = map(int, bbox)

#         if x < 0 or y < 0 or x + w > IM_WIDTH or y + h > IM_HEIGHT:
#             to_remove.append(tid)
#             continue

#         track['last_bbox'] = [x, y, w, h]
#         cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
#         cv2.putText(display, f"ID {tid}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

#     for tid in to_remove:
#         del trackers[tid]

#     latest_frame = display
#     out.write(display)
#     return display / 255.0

# # === SPAWN TRAFFIC ===
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

# # === MAIN ROUTINE ===
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






























# # === Enhanced CARLA + YOLOv5 + SiamMask Integration ===
# # Includes YOLOv5 detection, SiamMask tracking, semantic cam

# import glob
# import os
# import sys
# import time
# import cv2
# import numpy as np
# import random
# import math
# import torch
# from collections import defaultdict

# import carla
# from ultralytics import YOLO

# # === PATH SETUP ===
# carla_root = "C:/carla/CARLA0.9.15"
# siammask_root = "C:/carla/CARLA0.9.15/SiamMask"  # Update if different
# sys.path += [
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"),
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"),
#     os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"),
#     os.path.join(siammask_root),
#     os.path.join(siammask_root, "models"),
#     os.path.join(siammask_root, "experiments", "siammask_sharp"),
#     os.path.join(siammask_root, "utils"),
#     os.path.join(siammask_root, "tools")
# ]

# from agents.navigation.global_route_planner import GlobalRoutePlanner
# from agents.tools.misc import distance_vehicle

# # === SiamMask Setup ===
# from experiments.siammask_sharp.custom import Custom as SiamMaskCustom
# from tools.test import siamese_init, siamese_track
# from utils.load_config import load_config
# from types import SimpleNamespace

# torch.set_grad_enabled(False)
# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# pretrained_path = os.path.join(siammask_root, "experiments", "siammask_sharp", "SiamMask_VOT.pth")
# cfg = load_config(SimpleNamespace(config=os.path.join(siammask_root, "experiments", "siammask_sharp", "config_VOT18.json")))
# siammask = SiamMaskCustom(anchors=cfg['anchors'])
# siammask = load_pretrain(siammask, pretrained_path)
# siammask = siammask.eval().to(device)

# # === GLOBALS ===
# IM_WIDTH, IM_HEIGHT, IM_CHANNEL = 1280, 720, 4
# FOV = 105
# actor_list = []
# model_yolo = YOLO("yolov5su.pt")
# tracker_id_counter = 0
# trackers = dict()  # {id: {tracker, last_bbox}}
# detected_ids = set()

# # === Output Video ===
# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('yolo_siammask_output.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))
# latest_frame = None

# # === IMAGE PROCESSING ===
# def process_img(frame):
#     global latest_frame, tracker_id_counter, trackers

#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i_rgb = np.ascontiguousarray(i, dtype=np.uint8)
#     display = i_rgb.copy()

#     # === YOLO DETECTION ===
#     results = model_yolo(i_rgb, verbose=False)
#     new_detections = []

#     if results and hasattr(results[0], 'boxes'):
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:  # vehicle classes
#                 bbox = [x1, y1, x2 - x1, y2 - y1]
#                 center = (x1 + x2) // 2, (y1 + y2) // 2
#                 duplicate = False
#                 for track in trackers.values():
#                     tx, ty, tw, th = map(int, track['last_bbox'])
#                     if abs(center[0] - (tx + tw // 2)) < 50 and abs(center[1] - (ty + th // 2)) < 50:
#                         duplicate = True
#                         break
#                 if not duplicate:
#                     new_detections.append(bbox)

#     # === INITIATE NEW TRACKS ===
#     for bbox in new_detections:
#         x, y, w, h = map(int, bbox)
#         target_pos = np.array([x + w / 2, y + h / 2])
#         target_sz = np.array([w, h])
#         state = siamese_init(i_rgb, target_pos, target_sz, siammask)
#         trackers[tracker_id_counter] = {'state': state, 'last_bbox': bbox}
#         tracker_id_counter += 1

#     # === TRACK EXISTING ===
#     to_remove = []
#     for tid, track in trackers.items():
#         state = track['state']
#         state = siamese_track(state, i_rgb, mask_enable=True, refine_enable=True)
#         track['state'] = state
#         bbox = state['target_pos'] - state['target_sz'] / 2
#         bbox = np.concatenate([bbox, state['target_sz']])
#         x, y, w, h = map(int, bbox)

#         if x < 0 or y < 0 or x + w > IM_WIDTH or y + h > IM_HEIGHT:
#             to_remove.append(tid)
#             continue

#         track['last_bbox'] = [x, y, w, h]
#         cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
#         cv2.putText(display, f"ID {tid}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

#     for tid in to_remove:
#         del trackers[tid]

#     latest_frame = display
#     out.write(display)
#     return display / 255.0

# # === SPAWN TRAFFIC ===
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

# # === MAIN ROUTINE ===
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




























# # === Enhanced CARLA + YOLOv5 + SiamMask Integration ===
# Includes YOLOv5 detection, SiamMask tracking, semantic cam

import os
import sys
import time
import cv2
import numpy as np
import random
import math
import torch

import carla
from ultralytics import YOLO

# === PATH SETUP ===
carla_root = "C:/carla/CARLA0.9.15"
siammask_root = "C:/carla/CARLA0.9.15/SiamMask"  # Update if different

sys.path.append(os.path.join(siammask_root, "models"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
sys.path.append(os.path.join(siammask_root))
sys.path.append(os.path.join(siammask_root, "experiments", "siammask_sharp"))
sys.path.append(os.path.join(siammask_root, "utils"))
sys.path.append(os.path.join(siammask_root, "tools"))

from agents.navigation.global_route_planner import GlobalRoutePlanner
from agents.tools.misc import distance_vehicle

# === SiamMask Setup ===
from SiamMask.experiments.siammask_sharp.custom import Custom as SiamMaskCustom
from SiamMask.tools.test import siamese_init, siamese_track
from SiamMask.utils.load_config import load_config
from types import SimpleNamespace

torch.set_grad_enabled(False)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

pretrained_path = os.path.join(siammask_root, "experiments", "siammask_sharp", "SiamMask_VOT.pth")
cfg = load_config(SimpleNamespace(config=os.path.join(siammask_root, "experiments", "siammask_sharp", "config_VOT18.json")))
siammask = SiamMaskCustom(anchors=cfg['anchors'])
siammask = load_pretrain(siammask, pretrained_path)
siammask = siammask.eval().to(device)

# === GLOBALS ===
IM_WIDTH, IM_HEIGHT, IM_CHANNEL = 1280, 720, 4
FOV = 105
actor_list = []
model_yolo = YOLO("yolov5su.pt")
tracker_id_counter = 0
trackers = dict()  # {id: {tracker, last_bbox}}
detected_ids = set()

# === Output Video ===
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('yolo_siammask_output.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))
latest_frame = None

# === IMAGE PROCESSING ===
def process_img(frame):
    global latest_frame, tracker_id_counter, trackers

    frame.convert(carla.ColorConverter.CityScapesPalette)
    i = np.array(frame.raw_data).astype('uint8')
    i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
    i_rgb = np.ascontiguousarray(i, dtype=np.uint8)
    display = i_rgb.copy()

    # === YOLO DETECTION ===
    results = model_yolo(i_rgb, verbose=False)
    new_detections = []

    if results and hasattr(results[0], 'boxes'):
        for box in results[0].boxes.data.tolist():
            x1, y1, x2, y2, conf, cls = map(int, box[:6])
            if cls in [2, 3, 7]:  # vehicle classes
                bbox = [x1, y1, x2 - x1, y2 - y1]
                center = (x1 + x2) // 2, (y1 + y2) // 2
                duplicate = False
                for track in trackers.values():
                    tx, ty, tw, th = map(int, track['last_bbox'])
                    if abs(center[0] - (tx + tw // 2)) < 50 and abs(center[1] - (ty + th // 2)) < 50:
                        duplicate = True
                        break
                if not duplicate:
                    new_detections.append(bbox)

    # === INITIATE NEW TRACKS ===
    for bbox in new_detections:
        x, y, w, h = map(int, bbox)
        target_pos = np.array([x + w / 2, y + h / 2])
        target_sz = np.array([w, h])
        state = siamese_init(i_rgb, target_pos, target_sz, siammask)
        trackers[tracker_id_counter] = {'state': state, 'last_bbox': bbox}
        tracker_id_counter += 1

    # === TRACK EXISTING ===
    to_remove = []
    for tid, track in trackers.items():
        state = track['state']
        state = siamese_track(state, i_rgb, mask_enable=True, refine_enable=True)
        track['state'] = state
        bbox = state['target_pos'] - state['target_sz'] / 2
        bbox = np.concatenate([bbox, state['target_sz']])
        x, y, w, h = map(int, bbox)

        if x < 0 or y < 0 or x + w > IM_WIDTH or y + h > IM_HEIGHT:
            to_remove.append(tid)
            continue

        track['last_bbox'] = [x, y, w, h]
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(display, f"ID {tid}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    for tid in to_remove:
        del trackers[tid]

    latest_frame = display
    out.write(display)
    return display / 255.0

# === SPAWN TRAFFIC ===
def spawn_traffic(client, num_vehicles=30):
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprints = blueprint_library.filter("vehicle.*")
    spawn_points = world.get_map().get_spawn_points()

    traffic_manager = client.get_trafficmanager(8000)
    traffic_manager.set_global_distance_to_leading_vehicle(2.0)

    vehicles_list = []
    for _ in range(num_vehicles):
        blueprint = random.choice(vehicle_blueprints)
        spawn_point = random.choice(spawn_points)
        vehicle = world.try_spawn_actor(blueprint, spawn_point)
        if vehicle:
            vehicle.set_autopilot(True, traffic_manager.get_port())
            vehicles_list.append(vehicle)
    print(f"Spawned {len(vehicles_list)} traffic vehicles.")
    return vehicles_list

# === MAIN ROUTINE ===
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter("mkz_2020")[0]
    spawn_point = world.get_map().get_spawn_points()[1]
    ego = world.spawn_actor(vehicle_bp, spawn_point)
    actor_list.append(ego)

    cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
    cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
    cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
    cam_bp.set_attribute("fov", str(FOV))
    cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
    cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
    actor_list.append(cam)
    cam.listen(lambda data: process_img(data))

    env_map = world.get_map()
    route_planner = GlobalRoutePlanner(env_map, 2.0)
    point_a = carla.Location(x=299.4, y=129.75, z=0.29)
    point_b = carla.Location(x=-2.02, y=209.42, z=-0.01)
    route = route_planner.trace_route(point_a, point_b)

    traffic = spawn_traffic(client, 50)
    actor_list.extend(traffic)

    spectator = world.get_spectator()
    spectator.set_transform(carla.Transform(
        spawn_point.location + carla.Location(x=-6, z=2),
        carla.Rotation(yaw=spawn_point.rotation.yaw)))

    def show_loop():
        while True:
            if latest_frame is not None:
                cv2.imshow("YOLO + SiamMask Tracking", latest_frame)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break

    import threading
    t = threading.Thread(target=show_loop, daemon=True)
    t.start()

    def follow_route(vehicle, route):
        for i in range(len(route)):
            if i + 5 < len(route):
                target_waypoint = route[i + 5][0].transform.location
            else:
                target_waypoint = route[-1][0].transform.location

            while True:
                location = vehicle.get_transform().location
                direction = target_waypoint - location
                distance = math.sqrt(direction.x**2 + direction.y**2)
                if distance < 2.0:
                    break
                angle = math.atan2(direction.y, direction.x)
                yaw = math.radians(vehicle.get_transform().rotation.yaw)
                yaw_diff = (angle - yaw + math.pi) % (2 * math.pi) - math.pi
                steer = max(-1.0, min(1.0, yaw_diff * 2.0))
                throttle = min(0.6, distance * 0.15)
                vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer))
                time.sleep(0.05)
        print("Route completed!")

    follow_route(ego, route)
    time.sleep(2)

finally:
    print("Cleaning up actors...")
    out.release()
    for actor in actor_list:
        if isinstance(actor, carla.Vehicle):
            actor.set_autopilot(False)
        actor.destroy()
    print("Cleanup complete.")

