# import glob
# import os
# import sys
# import time
# import subprocess

# # Fix path for CARLA modules
# carla_root = "C:/carla/CARLA0.9.15"
# sys.path.append(os.path.join(carla_root, "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "PythonAPI", "examples"))
# sys.path.append(os.path.join(carla_root, "PythonAPI", "examples", "agents"))  # Added for agents import

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print("\u274c Failed to import CARLA route planner modules:", e)
#     exit(1)

# try:
#     sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from scipy.ndimage import convolve
# from ultralytics import YOLO

# IM_WIDTH = 1920
# IM_HEIGHT = 1080
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# cv2.startWindowThread()
# cv2.namedWindow("CARLA Camera")

# # Updated semantic path to use Right Semantic RGB dataset
# semantic_root = "C:/carla/CARLA0.9.15/Right Semantic/data_2d_semantics/train/2013_05_28_drive_0000_sync/image_01/semantic_rgb"

# frame_counter = 0

# def process_img(frame):
#     global frame_counter
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))
#     i = i[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     # Debug path printing
#     semantic_path = os.path.join(semantic_root, f"{frame_counter + 250:010}.png")
#     print(f"[DEBUG] Looking for semantic image at: {semantic_path}")

#     if os.path.exists(semantic_path):
#         overlay = cv2.imread(semantic_path)
#         if overlay is not None and overlay.shape == i.shape:
#             i = cv2.addWeighted(i, 0.6, overlay, 0.4, 0)
#         else:
#             print(f"[WARN] Overlay shape mismatch or failed to read: {semantic_path}")
#     else:
#         print(f"[WARN] Semantic image not found: {semantic_path}")

#     results = model.track(i, persist=True)
#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 label = f"Vehicle {conf:.2f}"
#                 cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     out.write(i)
#     cv2.imshow("CARLA Camera", i)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         return None

#     frame_counter += 1
#     return i / 255.0































# import glob
# import os
# import sys
# import time
# import subprocess
# import urllib.request
# import zipfile

# # ✅ Add proper CARLA paths
# carla_root = "C:/carla/CARLA0.9.15"
# PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# # ✅ Check manually extracted 'agents' folder
# if not os.path.exists(PythonAPI_agents_path):
#     print("❌ 'agents' module not found at expected location:", PythonAPI_agents_path)
#     print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
#     exit(1)

# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(PythonAPI_agents_path)

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print(f"❌ Failed to import CARLA route planner modules: {e}")
#     exit(0)

# try:
#     sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from ultralytics import YOLO

# IM_WIDTH = 1920
# IM_HEIGHT = 1080
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# def process_img(frame):
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     results = model.track(i, persist=True)

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 label = f"Vehicle {conf:.2f}"
#                 cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     out.write(i)
#     cv2.imshow("Semantic RGB Tracking", i)
#     cv2.waitKey(1)
#     return i / 255.0

# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for i in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"🚗 Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list

# try:
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()

#     blueprint_library = world.get_blueprint_library()
#     vehicle_bp = blueprint_library.filter("mkz_2020")[0]
#     spawn_point = world.get_map().get_spawn_points()[1]
#     ego = world.try_spawn_actor(vehicle_bp, spawn_point)
#     actor_list.append(ego)

#     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
#     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
#     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
#     cam_bp.set_attribute("fov", str(FOV))

#     cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
#     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
#     actor_list.append(cam)
#     cam.listen(lambda data: process_img(data))

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(
#         spawn_point.location + carla.Location(x=-6, z=2),
#         carla.Rotation(yaw=spawn_point.rotation.yaw)
#     ))

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     time.sleep(60)

# finally:
#     print("🧹 Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("✅ Cleanup complete.")
































# import glob
# import os
# import sys
# import time
# import subprocess
# import urllib.request
# import zipfile

# # ✅ Add proper CARLA paths
# carla_root = "C:/carla/CARLA0.9.15"
# PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# # ✅ Check manually extracted 'agents' folder
# if not os.path.exists(PythonAPI_agents_path):
#     print("❌ 'agents' module not found at expected location:", PythonAPI_agents_path)
#     print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
#     exit(1)

# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(PythonAPI_agents_path)

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print(f"❌ Failed to import CARLA route planner modules: {e}")
#     exit(0)

# try:
#     sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from ultralytics import YOLO

# IM_WIDTH = 1280
# IM_HEIGHT = 720
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# def process_img(frame):
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     results = model.track(i, persist=True)

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 label = f"Vehicle {conf:.2f}"
#                 cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     out.write(i)
#     cv2.imshow("Semantic RGB Tracking", i)
#     key = cv2.waitKey(1)
#     if key == ord('q'):
#         exit(0)
#     return i / 255.0

# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for i in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"🚗 Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list

# def follow_route(vehicle, route, world):
#     for i in range(len(route)):
#         target_location = route[i][0].transform.location
#         world.debug.draw_string(target_location, '^', draw_shadow=False,
#                                 color=carla.Color(r=0, g=255, b=0), life_time=30.0, persistent_lines=True)

#         vehicle_transform = vehicle.get_transform()
#         direction = target_location - vehicle_transform.location
#         distance = math.sqrt(direction.x**2 + direction.y**2)

#         if distance < 2.0:
#             continue

#         angle_to_target = math.atan2(direction.y, direction.x)
#         yaw = math.radians(vehicle_transform.rotation.yaw)
#         yaw_diff = (angle_to_target - yaw + math.pi) % (2 * math.pi) - math.pi

#         steer = max(-1.0, min(1.0, yaw_diff * 2.0))
#         throttle = max(0.3, min(0.6, distance * 0.1))

#         control = carla.VehicleControl(throttle=throttle, steer=steer, brake=0.0)
#         vehicle.apply_control(control)
#         time.sleep(0.1)

# try:
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()

#     blueprint_library = world.get_blueprint_library()
#     vehicle_bp = blueprint_library.filter("mkz_2020")[0]
#     spawn_point = world.get_map().get_spawn_points()[1]
#     ego = world.try_spawn_actor(vehicle_bp, spawn_point)
#     actor_list.append(ego)

#     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
#     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
#     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
#     cam_bp.set_attribute("fov", str(FOV))

#     cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
#     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
#     actor_list.append(cam)
#     cam.listen(lambda data: process_img(data))

#     map_ = world.get_map()
#     grp = GlobalRoutePlanner(map_, 2.0)
#     start = spawn_point.location
#     end = random.choice(map_.get_spawn_points()).location
#     route = grp.trace_route(start, end)

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(start + carla.Location(x=-6, z=2), carla.Rotation(yaw=spawn_point.rotation.yaw)))

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     follow_route(ego, route, world)
#     time.sleep(5)

# finally:
#     print("🧹 Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("✅ Cleanup complete.")






















# import glob
# import os
# import sys
# import time
# import subprocess
# import urllib.request
# import zipfile

# # ✅ Add proper CARLA paths
# carla_root = "C:/carla/CARLA0.9.15"
# PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# # ✅ Check manually extracted 'agents' folder
# if not os.path.exists(PythonAPI_agents_path):
#     print("❌ 'agents' module not found at expected location:", PythonAPI_agents_path)
#     print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
#     exit(1)

# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(PythonAPI_agents_path)

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print(f"❌ Failed to import CARLA route planner modules: {e}")
#     exit(0)

# try:
#     sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from ultralytics import YOLO

# IM_WIDTH = 1280
# IM_HEIGHT = 720
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# frame_updated = False


# def process_img(frame):
#     global frame_updated
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     results = model.track(i, persist=True)

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 label = f"Vehicle {conf:.2f}"
#                 cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     out.write(i)
#     cv2.imshow("Semantic RGB Tracking", i)
#     key = cv2.waitKey(1)
#     if key == ord('q'):
#         exit(0)

#     frame_updated = True
#     return i / 255.0


# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for i in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"🚗 Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list


# def follow_route(vehicle, route, world):
#     i = 0
#     while i < len(route):
#         target_location = route[i][0].transform.location
#         world.debug.draw_string(target_location, '^', draw_shadow=False,
#                                 color=carla.Color(r=0, g=255, b=0), life_time=1.0, persistent_lines=False)

#         vehicle_transform = vehicle.get_transform()
#         direction = target_location - vehicle_transform.location
#         distance = math.sqrt(direction.x**2 + direction.y**2)

#         if distance < 2.5:
#             i += 1
#             continue

#         angle_to_target = math.atan2(direction.y, direction.x)
#         yaw = math.radians(vehicle_transform.rotation.yaw)
#         yaw_diff = (angle_to_target - yaw + math.pi) % (2 * math.pi) - math.pi

#         steer = max(-1.0, min(1.0, yaw_diff * 2.0))
#         throttle = max(0.3, min(0.6, distance * 0.1))

#         control = carla.VehicleControl(throttle=throttle, steer=steer, brake=0.0)
#         vehicle.apply_control(control)

#         time.sleep(0.05)


# try:
#     client = carla.Client('localhost', 2000)
#     client.set_timeout(10.0)
#     world = client.get_world()

#     blueprint_library = world.get_blueprint_library()
#     vehicle_bp = blueprint_library.filter("mkz_2020")[0]
#     spawn_point = world.get_map().get_spawn_points()[1]
#     ego = world.try_spawn_actor(vehicle_bp, spawn_point)
#     actor_list.append(ego)

#     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
#     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
#     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
#     cam_bp.set_attribute("fov", str(FOV))

#     cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
#     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
#     actor_list.append(cam)
#     cam.listen(lambda data: process_img(data))

#     map_ = world.get_map()
#     grp = GlobalRoutePlanner(map_, 2.0)
#     start = spawn_point.location
#     end = random.choice(map_.get_spawn_points()).location
#     route = grp.trace_route(start, end)

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(start + carla.Location(x=-6, z=2), carla.Rotation(yaw=spawn_point.rotation.yaw)))

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     follow_route(ego, route, world)

#     time.sleep(2)

# finally:
#     print("🧹 Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("✅ Cleanup complete.")























# import glob
# import os
# import sys
# import time
# import subprocess
# import urllib.request
# import zipfile

# # ✅ Add proper CARLA paths
# carla_root = "C:/carla/CARLA0.9.15"
# PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# # ✅ Check manually extracted 'agents' folder
# if not os.path.exists(PythonAPI_agents_path):
#     print("❌ 'agents' module not found at expected location:", PythonAPI_agents_path)
#     print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
#     exit(1)

# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(PythonAPI_agents_path)

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print(f"❌ Failed to import CARLA route planner modules: {e}")
#     exit(0)

# try:
#     sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from ultralytics import YOLO

# IM_WIDTH = 1280
# IM_HEIGHT = 720
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# frame_updated = False


# def process_img(frame):
#     global frame_updated
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     results = model.track(i, persist=True)

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [2, 3, 7]:
#                 label = f"Vehicle {conf:.2f}"
#                 cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     out.write(i)
#     cv2.imshow("Semantic RGB Tracking", i)
#     key = cv2.waitKey(1)
#     if key == ord('q'):
#         exit(0)

#     frame_updated = True
#     return i / 255.0


# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for i in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"🚗 Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list


# def follow_route(vehicle, route):
#     for i in range(len(route)):
#         if i + 5 < len(route):
#             target_waypoint = route[i + 5][0].transform.location
#         else:
#             target_waypoint = route[-1][0].transform.location

#         while True:
#             vehicle_transform = vehicle.get_transform()
#             location = vehicle_transform.location

#             direction = target_waypoint - location
#             distance = math.sqrt(direction.x**2 + direction.y**2)

#             if distance < 2.0:
#                 break

#             angle_to_waypoint = math.atan2(direction.y, direction.x)
#             yaw_vehicle = math.radians(vehicle_transform.rotation.yaw)
#             yaw_diff = (angle_to_waypoint - yaw_vehicle + math.pi) % (2 * math.pi) - math.pi

#             steer = max(-1.0, min(1.0, yaw_diff * 2.0))

#             turn_sensitivity = 4.0
#             turn_threshold = 0.3

#             if abs(yaw_diff) > turn_threshold:
#                 throttle = max(0.2, 0.5 - abs(yaw_diff) * turn_sensitivity)
#                 brake = min(0.3, abs(yaw_diff) * turn_sensitivity)
#             else:
#                 throttle = min(0.6, distance * 0.15)
#                 brake = 0.0

#             vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))

#             time.sleep(0.05)

#     print("Route completed!")


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
#     point_a = carla.Location(x=299.399994, y=129.750000, z=0.298577)
#     point_b = carla.Location(x=-2.028770, y=209.420395, z=-0.005630)
#     route = route_planner.trace_route(point_a, point_b)

#     for waypoint in route:
#         world.debug.draw_string(
#             waypoint[0].transform.location, '^', draw_shadow=False,
#             color=carla.Color(r=0, g=255, b=0), life_time=50.0,
#             persistent_lines=True
#         )

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(
#         spawn_point.location + carla.Location(x=-6, z=2),
#         carla.Rotation(yaw=spawn_point.rotation.yaw)
#     ))

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     follow_route(ego, route)

#     time.sleep(2)

# finally:
#     print("🧹 Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("✅ Cleanup complete.")
















# # Perfect Till Now (This Code)


import glob
import os
import sys
import time
import subprocess
import urllib.request
import zipfile

# Add proper CARLA paths
carla_root = "C:/carla/CARLA0.9.15"
PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# Check manually extracted 'agents' folder
if not os.path.exists(PythonAPI_agents_path):
    print("'agents' module not found at expected location:", PythonAPI_agents_path)
    print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
    exit(1)

sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
sys.path.append(PythonAPI_agents_path)
# sys.path.append(os.path.join(siammask_root))  # Ensure 'models' can be imported


try:
    from agents.navigation.global_route_planner import GlobalRoutePlanner
    from agents.tools.misc import distance_vehicle
except ImportError as e:
    print(f"Failed to import CARLA route planner modules: {e}")
    exit(0)

try:
    sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
except IndexError:
    pass

import carla
import cv2
import random
import numpy as np
import math
from ultralytics import YOLO

IM_WIDTH = 1280
IM_HEIGHT = 720
IM_CHANNEL = 4
FOV = 105
actor_list = []
model = YOLO("yolov5su.pt")

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

latest_frame = None


def process_img(frame):
    global latest_frame
    frame.convert(carla.ColorConverter.CityScapesPalette)
    i = np.array(frame.raw_data).astype('uint8')
    i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
    i = np.ascontiguousarray(i, dtype=np.uint8)

    results = model.track(i, persist=True)

    if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
        for box in results[0].boxes.data.tolist():
            x1, y1, x2, y2, conf, cls = map(int, box[:6])
            if cls in [2, 3, 7]:
                label = f"Vehicle {conf:.2f}"
                cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    latest_frame = i
    out.write(i)
    return i / 255.0


def spawn_traffic(client, num_vehicles=30):
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprints = blueprint_library.filter("vehicle.*")
    spawn_points = world.get_map().get_spawn_points()

    traffic_manager = client.get_trafficmanager(8000)
    traffic_manager.set_global_distance_to_leading_vehicle(2.0)

    vehicles_list = []
    for i in range(num_vehicles):
        blueprint = random.choice(vehicle_blueprints)
        spawn_point = random.choice(spawn_points)
        vehicle = world.try_spawn_actor(blueprint, spawn_point)
        if vehicle:
            vehicle.set_autopilot(True, traffic_manager.get_port())
            vehicles_list.append(vehicle)
    print(f"Spawned {len(vehicles_list)} traffic vehicles.")
    return vehicles_list


def follow_route(vehicle, route):
    for i in range(len(route)):
        if i + 5 < len(route):
            target_waypoint = route[i + 5][0].transform.location
        else:
            target_waypoint = route[-1][0].transform.location

        while True:
            vehicle_transform = vehicle.get_transform()
            location = vehicle_transform.location

            direction = target_waypoint - location
            distance = math.sqrt(direction.x**2 + direction.y**2)

            if distance < 2.0:
                break

            angle_to_waypoint = math.atan2(direction.y, direction.x)
            yaw_vehicle = math.radians(vehicle_transform.rotation.yaw)
            yaw_diff = (angle_to_waypoint - yaw_vehicle + math.pi) % (2 * math.pi) - math.pi

            steer = max(-1.0, min(1.0, yaw_diff * 2.0))

            turn_sensitivity = 4.0
            turn_threshold = 0.3

            if abs(yaw_diff) > turn_threshold:
                throttle = max(0.2, 0.5 - abs(yaw_diff) * turn_sensitivity)
                brake = min(0.3, abs(yaw_diff) * turn_sensitivity)
            else:
                throttle = min(0.6, distance * 0.15)
                brake = 0.0

            vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))

            time.sleep(0.05)

    print("Route completed!")


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
    point_a = carla.Location(x=299.399994, y=129.750000, z=0.298577)
    point_b = carla.Location(x=-2.028770, y=209.420395, z=-0.005630)
    route = route_planner.trace_route(point_a, point_b)

    for waypoint in route:
        world.debug.draw_string(
            waypoint[0].transform.location, '^', draw_shadow=False,
            color=carla.Color(r=0, g=255, b=0), life_time=50.0,
            persistent_lines=True
        )

    spectator = world.get_spectator()
    spectator.set_transform(carla.Transform(
        spawn_point.location + carla.Location(x=-6, z=2),
        carla.Rotation(yaw=spawn_point.rotation.yaw)
    ))

    traffic = spawn_traffic(client, 50)
    actor_list.extend(traffic)

    # Start a loop to show the live image updates
    def show_loop():
        while True:
            if latest_frame is not None:
                cv2.imshow("Semantic RGB Tracking", latest_frame)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break

    import threading
    t = threading.Thread(target=show_loop, daemon=True)
    t.start()

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

















# # Trying this

# import glob
# import os
# import sys
# import time
# import subprocess
# import urllib.request
# import zipfile

# # ✅ Add proper CARLA paths
# carla_root = "C:/carla/CARLA0.9.15"
# PythonAPI_agents_path = os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples")

# # ✅ Check manually extracted 'agents' folder
# if not os.path.exists(PythonAPI_agents_path):
#     print("❌ 'agents' module not found at expected location:", PythonAPI_agents_path)
#     print("Please make sure you extracted CARLA fully and have the 'agents' folder.")
#     exit(1)

# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(PythonAPI_agents_path)

# try:
#     from agents.navigation.global_route_planner import GlobalRoutePlanner
#     from agents.tools.misc import distance_vehicle
# except ImportError as e:
#     print(f"❌ Failed to import CARLA route planner modules: {e}")
#     exit(0)

# try:
#     sys.path.append(glob.glob(os.path.join(carla_root, 'dist', 'carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64')))[0])
# except IndexError:
#     pass

# import carla
# import cv2
# import random
# import numpy as np
# import math
# from ultralytics import YOLO

# IM_WIDTH = 1280
# IM_HEIGHT = 720
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []
# model = YOLO("yolov5su.pt")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('test_yolov5_semantic.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# latest_frame = None
# tracked_objects = {}


# def process_img(frame):
#     global latest_frame, tracked_objects
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     i = np.array(frame.raw_data).astype('uint8')
#     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
#     i = np.ascontiguousarray(i, dtype=np.uint8)

#     results = model.track(i, persist=True, tracker="bytetrack.yaml")

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls, track_id = box[:7]
#             if int(cls) in [2, 3, 7]:
#                 center = ((x1 + x2) / 2, (y1 + y2) / 2)
#                 speed_kph = 0.0

#                 if int(track_id) in tracked_objects:
#                     prev_center, prev_time = tracked_objects[int(track_id)]
#                     dt = time.time() - prev_time
#                     speed_px = math.sqrt((center[0] - prev_center[0])**2 + (center[1] - prev_center[1])**2) / dt
#                     speed_kph = speed_px * 0.06  # Tuned factor for approx speed

#                 tracked_objects[int(track_id)] = (center, time.time())

#                 label = f"ID {int(track_id)} {speed_kph:.1f} km/h"
#                 cv2.rectangle(i, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
#                 cv2.putText(i, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     latest_frame = i
#     out.write(i)
#     return i / 255.0


# def spawn_traffic(client, num_vehicles=30):
#     world = client.get_world()
#     blueprint_library = world.get_blueprint_library()
#     vehicle_blueprints = blueprint_library.filter("vehicle.*")
#     spawn_points = world.get_map().get_spawn_points()

#     traffic_manager = client.get_trafficmanager(8000)
#     traffic_manager.set_global_distance_to_leading_vehicle(2.0)

#     vehicles_list = []
#     for i in range(num_vehicles):
#         blueprint = random.choice(vehicle_blueprints)
#         spawn_point = random.choice(spawn_points)
#         vehicle = world.try_spawn_actor(blueprint, spawn_point)
#         if vehicle:
#             vehicle.set_autopilot(True, traffic_manager.get_port())
#             vehicles_list.append(vehicle)
#     print(f"🚗 Spawned {len(vehicles_list)} traffic vehicles.")
#     return vehicles_list


# def follow_route(vehicle, route):
#     for i in range(len(route)):
#         if i + 5 < len(route):
#             target_waypoint = route[i + 5][0].transform.location
#         else:
#             target_waypoint = route[-1][0].transform.location

#         while True:
#             vehicle_transform = vehicle.get_transform()
#             location = vehicle_transform.location

#             direction = target_waypoint - location
#             distance = math.sqrt(direction.x**2 + direction.y**2)

#             if distance < 2.0:
#                 break

#             angle_to_waypoint = math.atan2(direction.y, direction.x)
#             yaw_vehicle = math.radians(vehicle_transform.rotation.yaw)
#             yaw_diff = (angle_to_waypoint - yaw_vehicle + math.pi) % (2 * math.pi) - math.pi

#             steer = max(-1.0, min(1.0, yaw_diff * 2.0))

#             turn_sensitivity = 4.0
#             turn_threshold = 0.3

#             if abs(yaw_diff) > turn_threshold:
#                 throttle = max(0.2, 0.5 - abs(yaw_diff) * turn_sensitivity)
#                 brake = min(0.3, abs(yaw_diff) * turn_sensitivity)
#             else:
#                 throttle = min(0.6, distance * 0.15)
#                 brake = 0.0

#             vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))

#             time.sleep(0.05)

#     print("Route completed!")


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
#     point_a = carla.Location(x=299.399994, y=129.750000, z=0.298577)
#     point_b = carla.Location(x=-2.028770, y=209.420395, z=-0.005630)
#     route = route_planner.trace_route(point_a, point_b)

#     for waypoint in route:
#         world.debug.draw_string(
#             waypoint[0].transform.location, '^', draw_shadow=False,
#             color=carla.Color(r=0, g=255, b=0), life_time=50.0,
#             persistent_lines=True
#         )

#     spectator = world.get_spectator()
#     spectator.set_transform(carla.Transform(
#         spawn_point.location + carla.Location(x=-6, z=2),
#         carla.Rotation(yaw=spawn_point.rotation.yaw)
#     ))

#     traffic = spawn_traffic(client, 50)
#     actor_list.extend(traffic)

#     def show_loop():
#         while True:
#             if latest_frame is not None:
#                 cv2.imshow("Semantic RGB Tracking", latest_frame)
#                 key = cv2.waitKey(1)
#                 if key == ord('q'):
#                     break

#     import threading
#     t = threading.Thread(target=show_loop, daemon=True)
#     t.start()

#     follow_route(ego, route)
#     time.sleep(2)

# finally:
#     print("🧹 Cleaning up actors...")
#     out.release()
#     for actor in actor_list:
#         if isinstance(actor, carla.Vehicle):
#             actor.set_autopilot(False)
#         actor.destroy()
#     print("✅ Cleanup complete.")