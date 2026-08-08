# # import sys
# # import os
# # import glob
# # import time
# # import threading
# # import random
# # import numpy as np
# # import math
# # import cv2
# # import torch
# # import importlib.util
# # import carla

# # # === Add SiamMask root and submodules to path ===
# # siammask_path = os.path.join("C:/carla/CARLA0.9.15/yolov5", "siammask")
# # sys.path.insert(0, siammask_path)
# # sys.path.insert(0, os.path.join(siammask_path, "experiments", "siammask_sharp"))

# # from custom import Custom

# # # === Carla and YOLO Config ===
# # IM_WIDTH = 1280
# # IM_HEIGHT = 720
# # IM_CHANNEL = 4
# # FOV = 105
# # actor_list = []

# # carla_root = "C:/carla/CARLA0.9.15"
# # yolov5_root = os.path.join(carla_root, "yolov5")
# # model_path = os.path.join(yolov5_root, "runs/train/exp2/weights/best.pt")

# # # === Add CARLA paths ===
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples", "agents"))

# # # ✅ Add YOLOv5 root to sys.path explicitly
# # if yolov5_root not in sys.path:
# #     sys.path.insert(0, yolov5_root)
# # os.chdir(yolov5_root)
# # print("🛠️ Changed working directory to:", os.getcwd())

# # # === Dynamically import YOLOv5 modules ===
# # def import_from_path(module_name, file_path):
# #     spec = importlib.util.spec_from_file_location(module_name, file_path)
# #     mod = importlib.util.module_from_spec(spec)
# #     spec.loader.exec_module(mod)
# #     return mod

# # try:
# #     utils_dir = os.path.join(yolov5_root, 'utils')
# #     common_path = os.path.join(yolov5_root, 'models', 'common.py')
# #     torch_utils_path = os.path.join(utils_dir, 'torch_utils.py')
# #     general_path = os.path.join(utils_dir, 'general.py')

# #     common = import_from_path("common", common_path)
# #     torch_utils = import_from_path("torch_utils", torch_utils_path)
# #     general = import_from_path("general", general_path)

# #     # Patch: handle missing TryExcept gracefully
# #     TryExcept = getattr(general, 'TryExcept', lambda *a, **kw: (lambda x: x))

# #     DetectMultiBackend = common.DetectMultiBackend
# #     select_device = torch_utils.select_device
# #     non_max_suppression = general.non_max_suppression
# #     scale_coords = general.scale_coords

# #     print("🔍 Loading YOLOv5 model from:", model_path)
# #     device = select_device('cpu')
# #     model = DetectMultiBackend(model_path, device=device, dnn=False, data=None, fp16=False)
# #     model.model.float().eval()
# # except Exception as e:
# #     normalized_path = os.path.normpath(str(e))
# #     print("❌ Failed to import YOLOv5 modules:", normalized_path)
# #     sys.exit(1)

# # # === Output video ===
# # output_video_path = os.path.join(carla_root, 'yolov5', 'tracked_output_custom.avi')
# # fourcc = cv2.VideoWriter_fourcc(*'XVID')
# # out = cv2.VideoWriter(output_video_path, fourcc, 20.0, (IM_WIDTH, IM_HEIGHT))

# # latest_frame = None

# # # === Initialize SiamMask ===
# # siammask = Custom()
# # siammask.eval().to(device)

# # tracking_targets = {}

# # def process_img(frame):
# #     global latest_frame
# #     frame.convert(carla.ColorConverter.CityScapesPalette)
# #     i = np.array(frame.raw_data).astype('uint8')
# #     i = i.reshape((IM_HEIGHT, IM_WIDTH, IM_CHANNEL))[:, :, :3]
# #     i = np.ascontiguousarray(i, dtype=np.uint8)

# #     try:
# #         im = i.copy()
# #         img = torch.from_numpy(im).permute(2, 0, 1).unsqueeze(0).to(device).float() / 255.0
# #         pred = model(img)
# #         pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45, classes=None, agnostic=False)

# #         for det in pred:
# #             if det is not None and len(det):
# #                 det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im.shape).round()
# #                 for *xyxy, conf, cls in det:
# #                     x1, y1, x2, y2 = map(int, xyxy)
# #                     cls = int(cls.item())
# #                     conf = float(conf.item())
# #                     if cls in [2, 3, 7]:
# #                         label = f"Vehicle {conf:.2f}"
# #                         cv2.rectangle(im, (x1, y1), (x2, y2), (255, 0, 0), 2)
# #                         cv2.putText(im, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
# #                         # TODO: Initialize SiamMask for tracking

# #     except Exception as e:
# #         print(f"⚠️ YOLOv5 prediction error:", e)

# #     latest_frame = im
# #     if im.shape[1] == IM_WIDTH and im.shape[0] == IM_HEIGHT:
# #         out.write(cv2.convertScaleAbs(im))
# #     return im / 255.0

# # def show_loop():
# #     while True:
# #         if latest_frame is not None:
# #             cv2.imshow("Semantic RGB Tracking", latest_frame)
# #             if cv2.waitKey(1) & 0xFF == ord('q'):
# #                 break

# # try:
# #     client = carla.Client('localhost', 2000)
# #     client.set_timeout(10.0)
# #     world = client.get_world()

# #     blueprint_library = world.get_blueprint_library()
# #     vehicle_bp = blueprint_library.filter("mkz_2020")[0]
# #     spawn_point = world.get_map().get_spawn_points()[1]
# #     ego = world.try_spawn_actor(vehicle_bp, spawn_point)
# #     actor_list.append(ego)

# #     spectator = world.get_spectator()
# #     spectator.set_transform(carla.Transform(
# #         spawn_point.location + carla.Location(x=-6, z=2),
# #         carla.Rotation(yaw=spawn_point.rotation.yaw)
# #     ))

# #     cam_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
# #     cam_bp.set_attribute("image_size_x", str(IM_WIDTH))
# #     cam_bp.set_attribute("image_size_y", str(IM_HEIGHT))
# #     cam_bp.set_attribute("fov", str(FOV))
# #     cam_transform = carla.Transform(carla.Location(x=0.75, z=1.25))
# #     cam = world.spawn_actor(cam_bp, cam_transform, attach_to=ego)
# #     actor_list.append(cam)
# #     cam.listen(lambda data: process_img(data))

# #     threading.Thread(target=show_loop, daemon=True).start()
# #     time.sleep(60)

# # finally:
# #     print("\nCleaning up actors...")
# #     out.release()
# #     for actor in actor_list:
# #         if isinstance(actor, carla.Vehicle):
# #             actor.set_autopilot(False)
# #         actor.destroy()
# #     print("Cleanup complete.")
# #     print(f"Video saved as: {output_video_path}")

























# # import sys
# # import os
# # import glob
# # import time
# # import threading
# # import random
# # import numpy as np
# # import math
# # import cv2
# # import torch
# # import importlib.util
# # import carla

# # # === Add SiamMask root and submodules to path ===
# # siammask_path = os.path.join("C:/carla/CARLA0.9.15/yolov5", "siammask")
# # sys.path.insert(0, siammask_path)
# # sys.path.insert(0, os.path.join(siammask_path, "experiments", "siammask_sharp"))

# # from custom import Custom

# # # === Carla and YOLO Config ===
# # IM_WIDTH = 1280
# # IM_HEIGHT = 720
# # IM_CHANNEL = 4
# # FOV = 105
# # actor_list = []

# # carla_root = "C:/carla/CARLA0.9.15"
# # yolov5_root = os.path.join(carla_root, "yolov5")
# # model_path = os.path.join(yolov5_root, "runs/train/exp2/weights/best.pt")

# # # === Add CARLA paths ===
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples", "agents"))

# # # ✅ Add YOLOv5 root to sys.path explicitly
# # if yolov5_root not in sys.path:
# #     sys.path.insert(0, yolov5_root)
# # os.chdir(yolov5_root)
# # print("🛠️ Changed working directory to:", os.getcwd())

# # # === Dynamically import YOLOv5 modules ===
# # def import_from_path(module_name, file_path):
# #     spec = importlib.util.spec_from_file_location(module_name, file_path)
# #     mod = importlib.util.module_from_spec(spec)
# #     spec.loader.exec_module(mod)
# #     return mod

# # try:
# #     utils_dir = os.path.join(yolov5_root, 'utils')
# #     common_path = os.path.join(yolov5_root, 'models', 'common.py')
# #     torch_utils_path = os.path.join(utils_dir, 'torch_utils.py')
# #     general_path = os.path.join(utils_dir, 'general.py')

# #     common = import_from_path("common", common_path)
# #     torch_utils = import_from_path("torch_utils", torch_utils_path)
# #     general = import_from_path("general", general_path)

# #     DetectMultiBackend = common.DetectMultiBackend
# #     select_device = torch_utils.select_device
# #     non_max_suppression = general.non_max_suppression
# #     scale_coords = general.scale_coords

# #     print("🔍 Loading YOLOv5 model from:", model_path)
# #     device = select_device('cpu')
# #     model = DetectMultiBackend(model_path, device=device, dnn=False, data=None, fp16=False)
# #     model.model.float().eval()
# # except Exception as e:
# #     normalized_path = os.path.normpath(str(e))
# #     print("❌ Failed to import YOLOv5 modules:", normalized_path)
# #     sys.exit(1)

# # # === Load SiamMask pretrained model ===
# # siammask_model_path = os.path.join(siammask_path, "SiamMask_DAVIS.pth")
# # if not os.path.exists(siammask_model_path):
# #     print("❌ SiamMask model file not found at:", siammask_model_path)
# #     sys.exit(1)

# # cfg_path = os.path.join(siammask_path, "experiments/siammask_sharp/config_davis.json")
# # siammask = Custom(anchors=None)  # Anchors will be set by load_model
# # siammask.load_model(siammask_model_path, cfg_path)
# # siammask.eval()
# # print("✅ SiamMask model loaded.")

























# # import sys
# # import os
# # import glob
# # import time
# # import threading
# # import random
# # import numpy as np
# # import math
# # import cv2
# # import torch
# # import importlib.util
# # import carla

# # # === Add SiamMask root and submodules to path ===
# # siammask_path = os.path.join("C:/carla/CARLA0.9.15/yolov5", "siammask")
# # sys.path.insert(0, siammask_path)
# # sys.path.insert(0, os.path.join(siammask_path, "experiments", "siammask_sharp"))

# # # === Carla and YOLO Config ===
# # IM_WIDTH = 1280
# # IM_HEIGHT = 720
# # IM_CHANNEL = 4
# # FOV = 105
# # actor_list = []

# # carla_root = "C:/carla/CARLA0.9.15"
# # yolov5_root = os.path.join(carla_root, "yolov5")
# # model_path = os.path.join(yolov5_root, "runs/train/exp2/weights/best.pt")

# # # === Add CARLA paths ===
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# # sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples", "agents"))

# # # Add YOLOv5 root to sys.path explicitly
# # if yolov5_root not in sys.path:
# #     sys.path.insert(0, yolov5_root)
    
# # # Save original working directory
# # original_dir = os.getcwd()
# # os.chdir(yolov5_root)
# # print("🛠️ Changed working directory to:", os.getcwd())

# # # === Dynamically import YOLOv5 modules ===
# # def import_from_path(module_name, file_path):
# #     try:
# #         spec = importlib.util.spec_from_file_location(module_name, file_path)
# #         if spec is None:
# #             print(f"❌ Failed to create spec for {module_name} from {file_path}")
# #             return None
# #         mod = importlib.util.module_from_spec(spec)
# #         spec.loader.exec_module(mod)
# #         return mod
# #     except Exception as e:
# #         print(f"❌ Error importing {module_name} from {file_path}: {e}")
# #         return None

# # # === Load YOLOv5 modules (Fix for scale_coords) ===
# # yolov5_loaded = True
# # try:
# #     # Check YOLOv5 version by checking if scale_coords is in general.py or in augmentations.py
# #     utils_dir = os.path.join(yolov5_root, 'utils')
# #     common_path = os.path.join(yolov5_root, 'models', 'common.py')
# #     torch_utils_path = os.path.join(utils_dir, 'torch_utils.py')
# #     general_path = os.path.join(utils_dir, 'general.py')
# #     augmentations_path = os.path.join(utils_dir, 'augmentations.py')  # New path for scale_coords in newer YOLOv5
    
# #     common = import_from_path("common", common_path)
# #     torch_utils = import_from_path("torch_utils", torch_utils_path)
# #     general = import_from_path("general", general_path)
    
# #     # Try to import scale_coords from augmentations if it's a newer YOLOv5 version
# #     scale_coords_found = False
# #     if os.path.exists(augmentations_path):
# #         augmentations = import_from_path("augmentations", augmentations_path)
# #         if hasattr(augmentations, 'scale_coords'):
# #             scale_coords = augmentations.scale_coords
# #             scale_coords_found = True
# #             print("✅ Found scale_coords in augmentations.py")
    
# #     # Try general if not found in augmentations
# #     if not scale_coords_found and hasattr(general, 'scale_coords'):
# #         scale_coords = general.scale_coords
# #         scale_coords_found = True
# #         print("✅ Found scale_coords in general.py")
    
# #     # If scale_coords still not found, we'll need a custom implementation
# #     if not scale_coords_found:
# #         print("⚠️ scale_coords not found in YOLOv5 modules, using custom implementation")
# #         def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
# #             # Rescale coords (xyxy) from img1_shape to img0_shape
# #             if ratio_pad is None:  # calculate from img0_shape
# #                 gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
# #                 pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
# #             else:
# #                 gain = ratio_pad[0][0]
# #                 pad = ratio_pad[1]

# #             coords[:, [0, 2]] -= pad[0]  # x padding
# #             coords[:, [1, 3]] -= pad[1]  # y padding
# #             coords[:, :4] /= gain
# #             coords[:, [0, 2]] = coords[:, [0, 2]].clamp(0, img0_shape[1])  # x1, x2
# #             coords[:, [1, 3]] = coords[:, [1, 3]].clamp(0, img0_shape[0])  # y1, y2
# #             return coords
    
# #     if all([common, torch_utils, general]):
# #         DetectMultiBackend = common.DetectMultiBackend
# #         select_device = torch_utils.select_device
# #         non_max_suppression = general.non_max_suppression
        
# #         print("🔍 Loading YOLOv5 model from:", model_path)
# #         device = select_device('cpu')  # Use CPU for compatibility with SiamMask
# #         model = DetectMultiBackend(model_path, device=device, dnn=False, data=None, fp16=False)
# #         model.model.float().eval()
# #         print("✅ YOLOv5 model loaded successfully")
# #     else:
# #         yolov5_loaded = False
# #         print("❌ Could not load all YOLOv5 modules")
# # except Exception as e:
# #     yolov5_loaded = False
# #     normalized_path = os.path.normpath(str(e))
# #     print(f"❌ Failed to import YOLOv5 modules: {normalized_path}")

# # # === Load SiamMask pretrained model (Fix for models.siammask_sharp) ===
# # try:
# #     # Go back to original directory before importing SiamMask
# #     os.chdir(original_dir)
    
# #     # Check if models directory exists in SiamMask path
# #     models_dir = os.path.join(siammask_path, "models")
# #     if not os.path.exists(models_dir):
# #         print(f"⚠️ 'models' directory not found in {siammask_path}")
# #         print(f"Creating symbolic link to experiments/siammask_sharp as models/siammask_sharp")
        
# #         # Create models directory if it doesn't exist
# #         os.makedirs(models_dir, exist_ok=True)
        
# #         # Create a symbolic link or copy the directory
# #         sharp_dir = os.path.join(siammask_path, "experiments", "siammask_sharp")
# #         dest_dir = os.path.join(models_dir, "siammask_sharp")
        
# #         try:
# #             # Try symbolic link first (requires admin privileges on Windows)
# #             if os.name == 'nt':  # Windows
# #                 import subprocess
# #                 subprocess.run(["mklink", "/D", dest_dir, sharp_dir], shell=True, check=True)
# #             else:  # Unix-like
# #                 os.symlink(sharp_dir, dest_dir)
# #             print("✅ Created symbolic link")
# #         except Exception as link_error:
# #             print(f"⚠️ Could not create symbolic link: {link_error}")
# #             print("Copying directory instead...")
            
# #             # If symbolic link fails, copy the directory
# #             import shutil
# #             shutil.copytree(sharp_dir, dest_dir)
# #             print("✅ Copied directory")
    
# #     # Add models directory to path if it exists now
# #     if os.path.exists(models_dir):
# #         sys.path.insert(0, models_dir)
    
# #     # Import the Custom class from SiamMask
# #     from custom import Custom
    
# #     siammask_model_path = os.path.join(siammask_path, "SiamMask_DAVIS.pth")
# #     if not os.path.exists(siammask_model_path):
# #         print("❌ SiamMask model file not found at:", siammask_model_path)
# #         siammask_loaded = False
# #     else:
# #         cfg_path = os.path.join(siammask_path, "experiments/siammask_sharp/config_davis.json")
# #         if not os.path.exists(cfg_path):
# #             print("❌ SiamMask config file not found at:", cfg_path)
# #             siammask_loaded = False
# #         else:
# #             # Force SiamMask to use the same device as YOLOv5
# #             siammask = Custom(anchors=None)
# #             siammask.load_model(siammask_model_path, cfg_path)
# #             siammask.eval()
            
# #             # Move to the same device as YOLOv5
# #             if yolov5_loaded:
# #                 siammask = siammask.to(device)
            
# #             print(f"✅ SiamMask model loaded on device: {next(siammask.parameters()).device}")
# #             siammask_loaded = True
            
# #             # Test SiamMask with dummy input
# #             try:
# #                 print("🧪 Testing SiamMask with dummy input...")
# #                 dummy_input = torch.randn(1, 3, 127, 127).to(device)  # Template size
# #                 dummy_search = torch.randn(1, 3, 255, 255).to(device)  # Search region
# #                 with torch.no_grad():
# #                     siammask.temple(dummy_input)
# #                     siammask.track(dummy_search)
# #                 print("✅ SiamMask model test passed")
# #             except Exception as e:
# #                 print(f"❌ SiamMask model test failed: {e}")
# # except Exception as e:
# #     siammask_loaded = False
# #     print(f"❌ Failed to load SiamMask: {e}")
# #     import traceback
# #     traceback.print_exc()

# # # === Helper functions for SiamMask tracking ===
# # def init_tracker(siammask, init_frame, init_bbox):
# #     """Initialize the SiamMask tracker with the first frame and bounding box
    
# #     Args:
# #         siammask: SiamMask tracker instance
# #         init_frame: First frame (numpy array, BGR format)
# #         init_bbox: Initial bounding box in format [x, y, w, h]
    
# #     Returns:
# #         state: Initial state dictionary for tracking
# #     """
# #     try:
# #         # Convert BGR to RGB (SiamMask expects RGB)
# #         init_frame_rgb = cv2.cvtColor(init_frame, cv2.COLOR_BGR2RGB)
        
# #         # Convert bbox [x, y, w, h] to [x, y, w, h] (no conversion needed)
# #         x, y, w, h = init_bbox
        
# #         # Initialize target at the center of the box
# #         target_pos = np.array([x + w/2, y + h/2])
# #         target_sz = np.array([w, h])
        
# #         # Initialize with the first frame
# #         state = siammask.init(init_frame_rgb, target_pos, target_sz)
# #         return state
# #     except Exception as e:
# #         print(f"❌ Tracker initialization failed: {e}")
# #         return None

# # def update_tracker(siammask, frame, state):
# #     """Update tracker with new frame
    
# #     Args:
# #         siammask: SiamMask tracker instance
# #         frame: Current frame (numpy array, BGR format)
# #         state: Tracker state from previous frame
    
# #     Returns:
# #         state: Updated state dictionary
# #         mask: Binary mask for target (numpy array)
# #         bbox: Bounding box in format [x, y, w, h]
# #     """
# #     try:
# #         # Convert BGR to RGB (SiamMask expects RGB)
# #         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
# #         # Update tracker
# #         state = siammask.track(frame_rgb, state)
        
# #         # Get mask and bbox
# #         mask = state['mask'] > state['p'].seg_thr
# #         bbox = state['ploygon'].astype(np.int32)
        
# #         # Convert polygon to rectangle [x, y, w, h]
# #         x, y, w, h = cv2.boundingRect(bbox)
# #         rect_bbox = [x, y, w, h]
        
# #         return state, mask, rect_bbox
# #     except Exception as e:
# #         print(f"❌ Tracker update failed: {e}")
# #         return state, None, None

# # # === Main function for demonstration ===
# # def main():
# #     """Main function for demonstrating SiamMask integration with CARLA and YOLOv5"""
# #     if not (yolov5_loaded and siammask_loaded):
# #         print("❌ Cannot proceed: YOLOv5 or SiamMask not loaded correctly")
# #         return
    
# #     try:
# #         # Initialize CARLA client
# #         client = carla.Client('localhost', 2000)
# #         client.set_timeout(10.0)
        
# #         # Get the world and setup
# #         world = client.get_world()
# #         settings = world.get_settings()
# #         settings.synchronous_mode = True
# #         settings.fixed_delta_seconds = 0.05
# #         world.apply_settings(settings)
        
# #         # Setup blueprint and spawn points
# #         blueprint_library = world.get_blueprint_library()
# #         vehicle_bp = blueprint_library.filter('model3')[0]
# #         spawn_points = world.get_map().get_spawn_points()
        
# #         # Spawn vehicle
# #         vehicle = world.spawn_actor(vehicle_bp, random.choice(spawn_points))
# #         actor_list.append(vehicle)
        
# #         # Setup camera
# #         camera_bp = blueprint_library.find('sensor.camera.rgb')
# #         camera_bp.set_attribute('image_size_x', str(IM_WIDTH))
# #         camera_bp.set_attribute('image_size_y', str(IM_HEIGHT))
# #         camera_bp.set_attribute('fov', str(FOV))
        
# #         # Spawn camera
# #         camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
# #         camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
# #         actor_list.append(camera)
        
# #         # Variables for tracking
# #         tracked_objects = {}
# #         next_id = 0
        
# #         # Process each camera frame
# #         def process_image(image):
# #             nonlocal tracked_objects, next_id
            
# #             # Convert CARLA image to numpy array
# #             array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
# #             array = np.reshape(array, (image.height, image.width, 4))
# #             array = array[:, :, :3]  # Remove alpha channel
            
# #             # Make a copy for drawing results
# #             display_image = array.copy()
            
# #             # Run YOLOv5 detection
# #             img = torch.from_numpy(array).to(device)
# #             img = img.permute(2, 0, 1).float().div(255.0).unsqueeze(0)
            
# #             pred = model(img)
# #             detections = non_max_suppression(pred[0], conf_thres=0.5, iou_thres=0.45)
            
# #             if len(detections) and len(detections[0]):
# #                 # Scale detections to image size
# #                 detections[0][:, :4] = scale_coords(img.shape[2:], detections[0][:, :4], array.shape).round()
                
# #                 # Process each detection
# #                 for det in detections[0]:
# #                     x1, y1, x2, y2, conf, cls = det.cpu().numpy()
                    
# #                     # Convert to [x, y, w, h] format
# #                     bbox = [int(x1), int(y1), int(x2-x1), int(y2-y1)]
                    
# #                     # Initialize new tracker if object is not being tracked
# #                     detection_center = np.array([x1 + (x2-x1)/2, y1 + (y2-y1)/2])
# #                     tracked = False
                    
# #                     # Check if detection matches any existing tracker
# #                     for obj_id, obj_data in list(tracked_objects.items()):
# #                         if obj_data['frames_since_update'] > 10:
# #                             # Remove trackers that haven't been updated
# #                             del tracked_objects[obj_id]
# #                             continue
                            
# #                         obj_bbox = obj_data['bbox']
# #                         obj_center = np.array([obj_bbox[0] + obj_bbox[2]/2, obj_bbox[1] + obj_bbox[3]/2])
                        
# #                         # Calculate distance between centers
# #                         dist = np.linalg.norm(detection_center - obj_center)
                        
# #                         # Update tracker if close enough
# #                         if dist < 50:  # Threshold for considering same object
# #                             state, mask, updated_bbox = update_tracker(siammask, array, obj_data['state'])
# #                             if updated_bbox is not None:
# #                                 tracked_objects[obj_id] = {
# #                                     'state': state,
# #                                     'bbox': updated_bbox,
# #                                     'class': cls,
# #                                     'frames_since_update': 0
# #                                 }
# #                             else:
# #                                 obj_data['frames_since_update'] += 1
# #                             tracked = True
# #                             break
                    
# #                     # Create new tracker if not tracked
# #                     if not tracked:
# #                         state = init_tracker(siammask, array, bbox)
# #                         if state is not None:
# #                             tracked_objects[next_id] = {
# #                                 'state': state,
# #                                 'bbox': bbox,
# #                                 'class': cls,
# #                                 'frames_since_update': 0
# #                             }
# #                             next_id += 1
            
# #             # Update all trackers
# #             for obj_id, obj_data in list(tracked_objects.items()):
# #                 state, mask, updated_bbox = update_tracker(siammask, array, obj_data['state'])
                
# #                 if updated_bbox is not None:
# #                     obj_data['state'] = state
# #                     obj_data['bbox'] = updated_bbox
# #                     obj_data['frames_since_update'] = 0
                    
# #                     # Draw tracking results
# #                     x, y, w, h = updated_bbox
# #                     cv2.rectangle(display_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
# #                     cv2.putText(display_image, f"ID: {obj_id}", (x, y-10), 
# #                                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
# #                     # Draw mask if available
# #                     if mask is not None:
# #                         display_image[:, :, 2] = np.where(mask, 255, display_image[:, :, 2])
# #                 else:
# #                     obj_data['frames_since_update'] += 1
            
# #             # Display results
# #             cv2.imshow("SiamMask Tracking", display_image)
# #             cv2.waitKey(1)
        
# #         # Register callback
# #         camera.listen(process_image)
        
# #         # Run for some time
# #         for _ in range(200):
# #             world.tick()
# #             time.sleep(0.05)

# #     except Exception as e:
# #         print(f"❌ Error in main function: {e}")
    
# #     finally:
# #         # Clean up
# #         print("Cleaning up...")
# #         cv2.destroyAllWindows()
# #         for actor in actor_list:
# #             actor.destroy()
# #         if 'settings' in locals():
# #             settings.synchronous_mode = False
# #             world.apply_settings(settings)

# # if __name__ == "__main__":
# #     main()






















# import sys
# import os
# import glob
# import time
# import threading
# import random
# import numpy as np
# import math
# import cv2
# import torch
# import importlib.util
# import carla

# # === Carla and YOLO Config ===
# IM_WIDTH = 1280
# IM_HEIGHT = 720
# IM_CHANNEL = 4
# FOV = 105
# actor_list = []

# carla_root = "C:/carla/CARLA0.9.15"
# yolov5_root = os.path.join(carla_root, "yolov5")
# model_path = os.path.join(yolov5_root, "runs/train/exp2/weights/best.pt")

# # === Add CARLA paths ===
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "carla"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples"))
# sys.path.append(os.path.join(carla_root, "WindowsNoEditor", "PythonAPI", "examples", "agents"))

# # Add YOLOv5 root to sys.path explicitly
# if yolov5_root not in sys.path:
#     sys.path.insert(0, yolov5_root)
    
# # Save original working directory
# original_dir = os.getcwd()
# os.chdir(yolov5_root)
# print("🛠️ Changed working directory to:", os.getcwd())

# # === Dynamically import YOLOv5 modules ===
# def import_from_path(module_name, file_path):
#     try:
#         spec = importlib.util.spec_from_file_location(module_name, file_path)
#         if spec is None:
#             print(f"❌ Failed to create spec for {module_name} from {file_path}")
#             return None
#         mod = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(mod)
#         return mod
#     except Exception as e:
#         print(f"❌ Error importing {module_name} from {file_path}: {e}")
#         return None

# # === Load YOLOv5 modules (Fix for scale_coords) ===
# yolov5_loaded = True
# try:
#     # Check YOLOv5 version by checking if scale_coords is in general.py or in augmentations.py
#     utils_dir = os.path.join(yolov5_root, 'utils')
#     common_path = os.path.join(yolov5_root, 'models', 'common.py')
#     torch_utils_path = os.path.join(utils_dir, 'torch_utils.py')
#     general_path = os.path.join(utils_dir, 'general.py')
#     augmentations_path = os.path.join(utils_dir, 'augmentations.py')  # New path for scale_coords in newer YOLOv5
    
#     common = import_from_path("common", common_path)
#     torch_utils = import_from_path("torch_utils", torch_utils_path)
#     general = import_from_path("general", general_path)
    
#     # Try to import scale_coords from augmentations if it's a newer YOLOv5 version
#     scale_coords_found = False
#     if os.path.exists(augmentations_path):
#         augmentations = import_from_path("augmentations", augmentations_path)
#         if hasattr(augmentations, 'scale_coords'):
#             scale_coords = augmentations.scale_coords
#             scale_coords_found = True
#             print("✅ Found scale_coords in augmentations.py")
    
#     # Try general if not found in augmentations
#     if not scale_coords_found and hasattr(general, 'scale_coords'):
#         scale_coords = general.scale_coords
#         scale_coords_found = True
#         print("✅ Found scale_coords in general.py")
    
#     # If scale_coords still not found, we'll need a custom implementation
#     if not scale_coords_found:
#         print("⚠️ scale_coords not found in YOLOv5 modules, using custom implementation")
#         def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
#             # Rescale coords (xyxy) from img1_shape to img0_shape
#             if ratio_pad is None:  # calculate from img0_shape
#                 gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
#                 pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
#             else:
#                 gain = ratio_pad[0][0]
#                 pad = ratio_pad[1]

#             coords[:, [0, 2]] -= pad[0]  # x padding
#             coords[:, [1, 3]] -= pad[1]  # y padding
#             coords[:, :4] /= gain
#             coords[:, [0, 2]] = coords[:, [0, 2]].clamp(0, img0_shape[1])  # x1, x2
#             coords[:, [1, 3]] = coords[:, [1, 3]].clamp(0, img0_shape[0])  # y1, y2
#             return coords
    
#     if all([common, torch_utils, general]):
#         DetectMultiBackend = common.DetectMultiBackend
#         select_device = torch_utils.select_device
#         non_max_suppression = general.non_max_suppression
        
#         print("🔍 Loading YOLOv5 model from:", model_path)
#         device = select_device('cpu')  # Use CPU for detection
#         model = DetectMultiBackend(model_path, device=device, dnn=False, data=None, fp16=False)
#         model.model.float().eval()
#         print("✅ YOLOv5 model loaded successfully")
#     else:
#         yolov5_loaded = False
#         print("❌ Could not load all YOLOv5 modules")
# except Exception as e:
#     yolov5_loaded = False
#     normalized_path = os.path.normpath(str(e))
#     print(f"❌ Failed to import YOLOv5 modules: {normalized_path}")

# # Simple object tracker based on IOU
# class SimpleTracker:
#     def __init__(self):
#         self.next_id = 0
#         self.tracked_objects = {}
        
#     def iou(self, boxA, boxB):
#         # Convert boxes to format [x1, y1, x2, y2]
#         boxA = [boxA[0], boxA[1], boxA[0] + boxA[2], boxA[1] + boxA[3]]
#         boxB = [boxB[0], boxB[1], boxB[0] + boxB[2], boxB[1] + boxB[3]]
        
#         # Determine the coordinates of the intersection rectangle
#         xA = max(boxA[0], boxB[0])
#         yA = max(boxA[1], boxB[1])
#         xB = min(boxA[2], boxB[2])
#         yB = min(boxA[3], boxB[3])
        
#         # Compute the area of intersection rectangle
#         interArea = max(0, xB - xA) * max(0, yB - yA)
        
#         # Compute the area of both bounding boxes
#         boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
#         boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        
#         # Compute the IOU
#         iou = interArea / float(boxAArea + boxBArea - interArea)
        
#         return iou
    
#     def update(self, detections):
#         # detections should be a list of [x, y, w, h, conf, cls] for each detection
#         # Returns dictionary with tracking IDs as keys and (bbox, class, conf) as values
        
#         # If no detections, update missing counts and return
#         if not detections:
#             for obj_id in list(self.tracked_objects.keys()):
#                 self.tracked_objects[obj_id]['frames_missing'] += 1
#                 if self.tracked_objects[obj_id]['frames_missing'] > 10:
#                     del self.tracked_objects[obj_id]
#             return self.tracked_objects
        
#         # Initialize arrays for tracking
#         matched_indices = []
#         unmatched_detections = list(range(len(detections)))
        
#         # For each tracked object, find the best matching detection
#         for obj_id, obj_data in list(self.tracked_objects.items()):
#             if obj_data['frames_missing'] > 10:
#                 del self.tracked_objects[obj_id]
#                 continue
                
#             best_iou = 0.3  # IOU threshold
#             best_index = -1
            
#             for i in unmatched_detections:
#                 det = detections[i]
#                 x1, y1, x2, y2, conf, cls = det
#                 det_bbox = [x1, y1, x2-x1, y2-y1]  # Convert to [x, y, w, h]
                
#                 current_iou = self.iou(obj_data['bbox'], det_bbox)
                
#                 if current_iou > best_iou:
#                     best_iou = current_iou
#                     best_index = i
            
#             # If we found a match, update the tracked object
#             if best_index >= 0:
#                 det = detections[best_index]
#                 x1, y1, x2, y2, conf, cls = det
#                 det_bbox = [int(x1), int(y1), int(x2-x1), int(y2-y1)]  # Convert to [x, y, w, h]
                
#                 self.tracked_objects[obj_id] = {
#                     'bbox': det_bbox,
#                     'class': cls,
#                     'conf': conf,
#                     'frames_missing': 0
#                 }
                
#                 matched_indices.append(best_index)
#                 unmatched_detections.remove(best_index)
#             else:
#                 # No match, increment missing count
#                 self.tracked_objects[obj_id]['frames_missing'] += 1
        
#         # For unmatched detections, create new tracked objects
#         for i in unmatched_detections:
#             det = detections[i]
#             x1, y1, x2, y2, conf, cls = det
#             det_bbox = [int(x1), int(y1), int(x2-x1), int(y2-y1)]  # Convert to [x, y, w, h]
            
#             self.tracked_objects[self.next_id] = {
#                 'bbox': det_bbox,
#                 'class': cls,
#                 'conf': conf,
#                 'frames_missing': 0
#             }
#             self.next_id += 1
        
#         return self.tracked_objects

# # Main function for demonstration
# def main():
#     """Main function for demonstrating YOLOv5 detection with CARLA"""
#     if not yolov5_loaded:
#         print("❌ Cannot proceed: YOLOv5 not loaded correctly")
#         return
    
#     try:
#         # Initialize CARLA client
#         client = carla.Client('localhost', 2000)
#         client.set_timeout(10.0)
        
#         # Get the world and setup
#         world = client.get_world()
#         settings = world.get_settings()
#         settings.synchronous_mode = True
#         settings.fixed_delta_seconds = 0.05
#         world.apply_settings(settings)
        
#         # Setup blueprint and spawn points
#         blueprint_library = world.get_blueprint_library()
#         vehicle_bp = blueprint_library.filter('model3')[0]
#         spawn_points = world.get_map().get_spawn_points()
        
#         # Spawn vehicle
#         vehicle = None
#         for spawn_point in spawn_points:
#             vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
#             if vehicle:
#                 actor_list.append(vehicle)
#                 break

#         if not vehicle:
#             raise RuntimeError("❌ Failed to spawn ego vehicle at any spawn point.")
        
#         # Setup camera
#         camera_bp = blueprint_library.find('sensor.camera.rgb')
#         camera_bp.set_attribute('image_size_x', str(IM_WIDTH))
#         camera_bp.set_attribute('image_size_y', str(IM_HEIGHT))
#         camera_bp.set_attribute('fov', str(FOV))
        
#         # Spawn camera
#         camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
#         camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
#         actor_list.append(camera)
        
#         # Initialize simple tracker
#         tracker = SimpleTracker()
        
#         # Process each camera frame
#         def process_image(image):
#             # Convert CARLA image to numpy array
#             array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
#             array = np.reshape(array, (image.height, image.width, 4))
#             array = array[:, :, :3]  # Remove alpha channel
            
#             # Make a copy for drawing results
#             display_image = array.copy()
            
#             # Run YOLOv5 detection
#             img = cv2.resize(array, (640, 640))  # YOLOv5 default size
#             img = torch.from_numpy(img).to(device)
#             img = img.permute(2, 0, 1).float().div(255.0).unsqueeze(0)

            
#             pred = model(img)
#             detections = non_max_suppression(pred[0], conf_thres=0.5, iou_thres=0.45)
            
#             # Process detections
#             detection_list = []
#             if len(detections) and len(detections[0]):
#                 # Scale detections to image size
#                 detections[0][:, :4] = scale_coords(img.shape[2:], detections[0][:, :4], array.shape).round()
                
#                 # Format detections for tracker
#                 for det in detections[0]:
#                     detection_list.append(det.cpu().numpy())
            
#             # Update tracker
#             tracked_objects = tracker.update(detection_list)
            
#             # Draw tracking results
#             for obj_id, obj_data in tracked_objects.items():
#                 if obj_data['frames_missing'] > 0:
#                     continue  # Skip drawing objects that are missing
                
#                 x, y, w, h = obj_data['bbox']
#                 cls = obj_data['class']
#                 conf = obj_data['conf']
                
#                 # Choose color based on class
#                 colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
#                 color = colors[int(cls) % len(colors)]
                
#                 # Draw bounding box
#                 cv2.rectangle(display_image, (x, y), (x+w, y+h), color, 2)
                
#                 # Draw label
#                 label = f"ID:{obj_id} C:{int(cls)} {conf:.2f}"
#                 cv2.putText(display_image, label, (x, y-10), 
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
#             # Display results
#             cv2.imshow("YOLOv5 Detection", display_image)
#             cv2.waitKey(1)
        
#         # Register callback
#         camera.listen(process_image)
        
#         # Run for some time
#         vehicle.set_autopilot(True)
#         print("✅ Running YOLOv5 detection demo. Press Ctrl+C to exit.")
        
#         # Spawn some other vehicles for testing
#         for _ in range(10):
#             other_vehicle = world.spawn_actor(
#                 blueprint_library.filter('vehicle.*')[random.randint(0, 10)],
#                 random.choice(spawn_points)
#             )
#             other_vehicle.set_autopilot(True)
#             actor_list.append(other_vehicle)
        
#         # Main loop
#         for _ in range(1000):  # Run for 1000 frames
#             world.tick()
#             time.sleep(0.05)

#     except KeyboardInterrupt:
#         print("👋 Demo stopped by user")
#     except Exception as e:
#         print(f"❌ Error in main function: {e}")
    
#     finally:
#         # Clean up
#         print("Cleaning up...")
#         cv2.destroyAllWindows()
#         for actor in actor_list:
#             if actor is not None:
#                 actor.destroy()
#         if 'settings' in locals():
#             settings.synchronous_mode = False
#             world.apply_settings(settings)

# if __name__ == "__main__":
#     main()















import os
import sys
import torch
from types import SimpleNamespace

# Fix SiamMask internal utils resolution
sys.path.insert(0, os.path.join("siammask", "utils"))

# === Add SiamMask paths ===
siammask_root = "C:/carla/CARLA0.9.15/yolov5/siammask"
sys.path.append(siammask_root)
sys.path.append(os.path.join(siammask_root, 'experiments', 'siammask_sharp'))
sys.path.append(os.path.join(siammask_root, 'utils'))
sys.path.append(os.path.join(siammask_root, 'tools'))
sys.path.append(os.path.join(siammask_root, 'models'))  # ✅ Added to fix model import issues

# === Import SiamMask core modules ===
from experiments.siammask_sharp.custom import Custom as SiamMaskCustom
from utils.load_config import load_config
from utils.load_helper import load_pretrain

# === Configuration and setup ===
pretrained_path = os.path.join(siammask_root, 'experiments', 'siammask_sharp', 'SiamMask_DAVIS.pth')
config_path = os.path.join(siammask_root, 'experiments', 'siammask_sharp', 'config_davis.json')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.set_grad_enabled(False)

# === Load SiamMask config and model ===
print("Loading SiamMask config from:", config_path)
cfg = load_config(SimpleNamespace(config=config_path))

print("Building SiamMask model...")
siammask = SiamMaskCustom(anchors=cfg['anchors'])
print("Loading pretrained weights from:", pretrained_path)
siammask = load_pretrain(siammask, pretrained_path)
siammask.eval().to(device)

print("SiamMask model loaded and ready on device:", device)
