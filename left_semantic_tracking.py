# from ultralytics import YOLO
# import cv2
# import carla
# import numpy as np

# # Load your trained YOLOv5 model
# model_path = "C:/carla/CARLA0.9.15/yolov5/runs/train/exp2/weights/best.pt"
# model = YOLO(model_path)

# # Your existing CARLA setup and capture code goes here...

# def process_img(frame):
#     frame.convert(carla.ColorConverter.CityScapesPalette)
#     img = np.array(frame.raw_data).astype('uint8')
#     img = img.reshape((frame.height, frame.width, 4))[:, :, :3]
#     img = np.ascontiguousarray(img)

#     results = model.track(img, persist=True)

#     if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
#         for box in results[0].boxes.data.tolist():
#             x1, y1, x2, y2, conf, cls = map(int, box[:6])
#             if cls in [0, 1, 2]:  # Adjust if your custom class ids differ
#                 label = f"{conf:.2f}"
#                 cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                             0.5, (0, 255, 0), 2)

#     cv2.imshow("YOLOv5 + Semantic", img)
#     if cv2.waitKey(1) == ord('q'):
#         return None
#     return img / 255.0

















import glob
import os
import sys
import time
import threading
import random
import numpy as np
import math
import cv2
import carla
from ultralytics import YOLO

# === Configuration ===
IM_WIDTH = 1280
IM_HEIGHT = 720
IM_CHANNEL = 4
FOV = 105
actor_list = []
latest_frame = None

# === Paths ===
carla_root = "C:/carla/CARLA0.9.15"
model_path = "C:/carla/CARLA0.9.15/yolov5/runs/train/exp2/weights/best.pt"  # left semantics model

# === Set up system paths ===
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples", "agents"))

from agents.navigation.global_route_planner import GlobalRoutePlanner

# === Load YOLOv5 model ===
print(f"Loading YOLOv5 model from: {model_path}")
model = YOLO(model_path)

# === Output video setup ===
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('left_semantic_tracking_output.avi', fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# === Process image frame from CARLA ===
def process_img(frame):
    global latest_frame
    frame.convert(carla.ColorConverter.CityScapesPalette)
    i = np.array(frame.raw_data).astype('uint8')
    i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
    i = np.ascontiguousarray(i, dtype=np.uint8)

    try:
        results = model.predict(i, stream=False)
        if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
            for box in results[0].boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = map(int, box[:6])
                if cls in [2, 3, 7]:
                    label = f"Vehicle {conf:.2f}"
                    cv2.rectangle(i, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(i, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    except Exception as e:
        print(f"⚠️ YOLOv5 prediction error: {e}")

    latest_frame = i
    out.write(cv2.convertScaleAbs(i))
    return i / 255.0

# === Live display loop ===
def show_loop():
    while True:
        if latest_frame is not None:
            cv2.imshow("Semantic RGB Tracking", latest_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# === Spawn traffic vehicles ===
def spawn_traffic(client, num_vehicles=30):
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    vehicles = []
    spawn_points = world.get_map().get_spawn_points()
    tm = client.get_trafficmanager(8000)
    tm.set_global_distance_to_leading_vehicle(2.0)
    for _ in range(num_vehicles):
        vehicle_bp = random.choice(bp_lib.filter("vehicle.*"))
        spawn_point = random.choice(spawn_points)
        v = world.try_spawn_actor(vehicle_bp, spawn_point)
        if v:
            v.set_autopilot(True, tm.get_port())
            vehicles.append(v)
    print(f"🚗 Spawned {len(vehicles)} vehicles.")
    return vehicles

# === Follow custom route ===
def follow_route(vehicle, route):
    for i in range(len(route)):
        if i + 5 < len(route):
            target = route[i + 5][0].transform.location
        else:
            target = route[-1][0].transform.location

        while True:
            location = vehicle.get_transform().location
            direction = target - location
            distance = math.sqrt(direction.x**2 + direction.y**2)
            if distance < 2.0:
                break

            angle = math.atan2(direction.y, direction.x)
            yaw = math.radians(vehicle.get_transform().rotation.yaw)
            yaw_diff = (angle - yaw + math.pi) % (2 * math.pi) - math.pi
            steer = max(-1.0, min(1.0, yaw_diff * 2.0))
            throttle = 0.4
            brake = 0.0
            vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))
            time.sleep(0.05)

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    # Ego vehicle
    vehicle_bp = blueprint_library.filter("mkz_2020")[0]
    spawn_point = world.get_map().get_spawn_points()[1]
    ego = world.try_spawn_actor(vehicle_bp, spawn_point)
    actor_list.append(ego)

    # Set spectator view
    spectator = world.get_spectator()
    spectator.set_transform(carla.Transform(spawn_point.location + carla.Location(x=-6, z=2), carla.Rotation(yaw=spawn_point.rotation.yaw)))

    # Left semantic camera
    cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
    cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
    cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
    cam_bp.set_attribute("fov", str(FOV))
    cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
    cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
    actor_list.append(cam)
    cam.listen(lambda data: process_img(data))

    # Spawn traffic
    actor_list.extend(spawn_traffic(client, 40))

    # Plan a custom route
    map_ = world.get_map()
    route_planner = GlobalRoutePlanner(map_, 2.0)
    route = route_planner.trace_route(spawn_point.location, random.choice(map_.get_spawn_points()).location)

    # Start display
    threading.Thread(target=show_loop, daemon=True).start()

    # Apply custom route (optional)
    follow_route(ego, route)

    # OR just run autopilot
    # ego.set_autopilot(True)

    time.sleep(10)

finally:
    print("\n🧹 Cleaning up actors...")
    out.release()
    for actor in actor_list:
        if isinstance(actor, carla.Vehicle):
            actor.set_autopilot(False)
        actor.destroy()
    print("✅ Cleanup complete.")
    print("📹 Video saved as: left_semantic_tracking_output.avi")
















