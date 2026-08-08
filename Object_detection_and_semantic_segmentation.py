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