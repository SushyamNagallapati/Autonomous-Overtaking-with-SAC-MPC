import sys
import os

# Add SiamMask root to path
siammask_root = "C:/carla/CARLA0.9.15/yolov5/siammask"
sys.path.insert(0, siammask_root)

# Run test.py from tools
test_path = os.path.join(siammask_root, "tools", "test.py")
exec(open(test_path).read())
