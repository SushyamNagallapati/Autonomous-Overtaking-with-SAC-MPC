import os
import sys
import torch
from types import SimpleNamespace
import cv2
import numpy as np
import importlib.util
import carla
import time

# === Add SiamMask paths ===
sys.path.append('SiamMask')
sys.path.append('SiamMask/experiments/siammask_sharp')
sys.path.append('SiamMask/utils')
sys.path.append('SiamMask/tools')

# === Paths ===
carla_root = "C:/carla/CARLA0.9.15"
yolov5_root = os.path.join(carla_root, "yolov5")
siammask_root = os.path.join(yolov5_root, "siammask")
model_path = os.path.join(yolov5_root, "runs", "train", "exp2", "weights", "best.pt")

# === Add paths ===
sys.path.extend([
    os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"),
    os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"),
    os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"),
    yolov5_root,
    siammask_root,
    os.path.join(siammask_root, "experiments", "siammask_sharp"),
    os.path.join(siammask_root, "utils"),
    os.path.join(siammask_root, "tools"),
    os.path.join(siammask_root, "models")
])

# === Import modules ===
from experiments.siammask_sharp.custom import Custom as SiamMaskCustom
from utils.load_config import load_config
from utils.load_helper import load_pretrain
from utils.bbox_helper import get_axis_aligned_bbox
from models.common import DetectMultiBackend
from utils.general import non_max_suppression
from utils.torch_utils import select_device
from augmentations import scale_coords
from cv2 import calcOpticalFlowFarneback

# === SiamMask setup ===
config_path = os.path.join(siammask_root, "experiments", "siammask_sharp", "config_davis.json")
pretrained_path = os.path.join(siammask_root, "experiments", "siammask_sharp", "SiamMask_DAVIS.pth")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.set_grad_enabled(False)

cfg = load_config(SimpleNamespace(config=config_path))
siammask = SiamMaskCustom(anchors=cfg['anchors'])
siammask = load_pretrain(siammask, pretrained_path).eval().to(device)

# === Setup YOLOv5 ===
device_yolo = select_device('cpu')
model = DetectMultiBackend(model_path, device=device_yolo, dnn=False)
model.model.float().eval()

# === Tracker storage ===
trackers = {}
next_track_id = 0
prev_gray = None

# === CARLA setup ===
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.get_world()
settings = world.get_settings()
settings.synchronous_mode = True
settings.fixed_delta_seconds = 0.05
world.apply_settings(settings)

blueprint_library = world.get_blueprint_library()
vehicle_bp = blueprint_library.filter('model3')[0]
spawn_point = world.get_map().get_spawn_points()[0]
vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
camera_bp = blueprint_library.find('sensor.camera.rgb')
camera_bp.set_attribute('image_size_x', '640')
camera_bp.set_attribute('image_size_y', '480')
camera_bp.set_attribute('fov', '105')
camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

actor_list = [vehicle, camera]

# === Detection and tracking logic ===
def process_image(image):
    global next_track_id, prev_gray
    array = np.frombuffer(image.raw_data, dtype=np.uint8).reshape((image.height, image.width, 4))[:, :, :3]
    display_image = array.copy()

    img = torch.from_numpy(display_image).to(device_yolo)
    img = img.permute(2, 0, 1).float().div(255.0).unsqueeze(0)
    pred = model(img)
    detections = non_max_suppression(pred[0], conf_thres=0.5, iou_thres=0.45)[0]

    if detections is not None and len(detections):
        detections[:, :4] = scale_coords(img.shape[2:], detections[:, :4], display_image.shape).round()

        for *xyxy, conf, cls in detections:
            x1, y1, x2, y2 = map(int, xyxy)
            w, h = x2 - x1, y2 - y1
            bbox = [x1, y1, w, h]

            already_tracked = False
            for tracker_id in trackers:
                tracker_state = trackers[tracker_id]
                if tracker_state.get('active', False):
                    tx, ty, tw, th = tracker_state['bbox']
                    iou = compute_iou((x1, y1, x2, y2), (tx, ty, tx+tw, ty+th))
                    if iou > 0.3:
                        already_tracked = True
                        break

            if not already_tracked:
                cx, cy, bw, bh = get_axis_aligned_bbox(bbox)
                pos = np.array([cx, cy])
                size = np.array([bw, bh])
                trackers[next_track_id] = siammask.init(display_image, pos, size, device=device)
                trackers[next_track_id]['active'] = True
                trackers[next_track_id]['bbox'] = bbox
                trackers[next_track_id]['history'] = [(cx, cy)]
                next_track_id += 1

    # Optical Flow
    gray = cv2.cvtColor(display_image, cv2.COLOR_BGR2GRAY)
    if prev_gray is not None:
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    else:
        flow = np.zeros_like(display_image, dtype=np.float32)
    prev_gray = gray

    # Update trackers
    for tracker_id, state in list(trackers.items()):
        state = siammask.track(state, display_image)
        pos = tuple(state['target_pos'])
        sz = tuple(state['target_sz'])
        bbox = state['target_pos'], state['target_sz']
        res = state['ploygon']

        x, y = int(pos[0]), int(pos[1])
        trackers[tracker_id]['bbox'] = [x - int(sz[0]/2), y - int(sz[1]/2), int(sz[0]), int(sz[1])]

        history = trackers[tracker_id].setdefault('history', [])
        history.append((x, y))
        if len(history) > 10:
            history.pop(0)

        velocity = (0, 0)
        acceleration = (0, 0)
        if len(history) >= 2:
            dx = history[-1][0] - history[-2][0]
            dy = history[-1][1] - history[-2][1]
            velocity = (dx / 0.05, dy / 0.05)
        if len(history) >= 3:
            dvx = (history[-1][0] - history[-2][0]) - (history[-2][0] - history[-3][0])
            dvy = (history[-1][1] - history[-2][1]) - (history[-2][1] - history[-3][1])
            acceleration = (dvx / 0.05, dvy / 0.05)

        cv2.polylines(display_image, [np.int0(res)], True, (0, 255, 0), 2)
        cv2.putText(display_image, f"ID:{tracker_id} V:{velocity[0]:.1f},{velocity[1]:.1f}", (x, y-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    cv2.imshow("YOLO + SiamMask + Velocity", display_image)
    cv2.waitKey(1)

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    return interArea / float(boxAArea + boxBArea - interArea)

camera.listen(lambda image: process_image(image))

try:
    vehicle.set_autopilot(True)
    print("Running YOLO + SiamMask tracking in CARLA. Press Ctrl+C to stop.")
    while True:
        world.tick()
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    for actor in actor_list:
        if actor is not None:
            actor.destroy()
    cv2.destroyAllWindows()