# Leeds Station Service Robot — Python Simulation

This project is a **Python-based software simulation prototype** of a railway station service robot. It integrates a **PyQt6 graphical user interface (GUI), voice interaction, YOLOv8n object detection, and fixed-priority task control**.

> **Note:** This is a software simulation, not a robot deployed in a physical station. Navigation is simulated through state changes and voice announcements. Camera-based proximity detection uses an image-size ratio threshold and does not provide precise physical distance measurements.

## 1. Main Features

| Priority | Task | Description |
| --- | --- | --- |
| P0 (3, highest) | Emergency Assistance | Emergency button and spoken assistance messages |
| P1 (2) | Voice Inquiry | Speech recognition and keyword matching for destination or staff enquiries |
| P2 (1) | Proximity Warning | Requests a warning when a detected bounding box exceeds a height-ratio threshold |
| P3 (0, lowest) | Routine Patrol | Scheduled patrol announcements |

The system compares incoming and current numerical task priorities to decide whether to accept a request. It uses `QTimer`, state variables, and threads to coordinate the GUI, speech playback, and task transitions.

## 2. Project Files

```text
Leeds-Station-Robot/
├── voice.py             # PyQt6 GUI, voice interaction, and priority-based task control
├── camera_module.py     # OpenCV camera, YOLOv8n detection, and P2 proximity checks
├── README.md            # Project documentation
├── requirements.txt     # Python package dependencies
├── .gitignore           # Files excluded from Git version control
└── yolov8n.pt           # Optional local pretrained weights; can be downloaded automatically
```

The filenames above reflect this project's current Python scripts. Adjust the commands below if your local filenames differ. The `yolov8n.pt` weights are optional locally and should generally not be committed to the repository.

## 3. Requirements and Installation

You need Python and a working camera. P1 voice input also requires a microphone and compatible audio dependencies.

Creating a virtual environment in the project directory is recommended:

```bash
python -m venv .venv
```

Activate it:

- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

Install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Alternatively, install the main packages directly:

```bash
python -m pip install PyQt6 ultralytics opencv-python pyttsx3 SpeechRecognition
```

Microphone-based recognition typically requires a compatible audio-input package such as `PyAudio`. Its installation requirements can vary with the operating system and Python version.

## 4. What Is YOLOv8n, and How Do I Obtain It?

### 4.1 About the Model

**YOLO** stands for *You Only Look Once*. It is a family of models used for computer vision tasks. In **YOLOv8n**, the `n` stands for *nano*: a lightweight version of YOLOv8 suitable for real-time detection experiments.

This project uses **`yolov8n.pt`, pretrained object-detection weights published by Ultralytics**. The model was not trained from scratch as part of this project. The standard COCO-pretrained detection model supports **80 object classes**, including `person`, `bicycle`, `car`, `train`, `backpack`, and `suitcase`.

- **COCO:** A publicly available dataset used to train and evaluate object-detection models.
- **`.pt`:** A common file format for PyTorch model weights.
- **Inference:** Using a trained model to make predictions on new camera images.
- **This project's contribution:** Connecting predictions from the pretrained model to custom proximity-detection logic and the robot's P2 priority-control workflow.

### 4.2 Recommended: Automatic Download

Ultralytics can usually retrieve the official model weights automatically the first time they are needed. After installing `ultralytics`, run the following from the project directory:

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
```

If the weights are not already available locally, Ultralytics will **usually download them from its official model resources**. An internet connection is normally required for the first download. Once the weights have been obtained, they can be loaded locally without training the model yourself.

You can also test loading from a terminal:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); print('YOLOv8n loaded successfully')"
```

### 4.3 Manual Download

If automatic downloading fails, obtain the weights through an **official Ultralytics distribution channel**, and place the file in the project directory or specify its complete path in your code:

- YOLOv8 official documentation: https://docs.ultralytics.com/models/yolov8/
- Ultralytics official model assets: https://github.com/ultralytics/assets/releases
- Ultralytics YOLOv8 models on Hugging Face: https://huggingface.co/Ultralytics/YOLOv8

Make sure the file is named **`yolov8n.pt`** (the object-detection model), rather than weights for another task, such as `yolov8n-seg.pt`.

After downloading, load the file with:

```python
model_path = "yolov8n.pt"
model = YOLO(model_path)
```

**Path reminder:** A relative path such as `"yolov8n.pt"` is normally resolved from the **current working directory**, which is not necessarily the same as the directory containing the `.py` file. It is easiest to change into the project directory before running the script. Otherwise, use an absolute path or construct one relative to `__file__`.

**You do not need the full COCO dataset** just to run inference using the official pretrained weights. The dataset would be relevant mainly for training, fine-tuning, or particular evaluation tasks.

## 5. How to Run

Open a terminal in the directory containing `voice.py` and `camera_module.py`.

### 5.1 Voice GUI Only

```bash
python voice.py
```

This launches the PyQt6 robot interface, with P0, P1, and P2 buttons for demonstrating the corresponding interactions.

### 5.2 Voice GUI and YOLO Camera Detection

```bash
python camera_module.py
```

The script attempts to:

1. Create the `QApplication` and `LeedsStationRobot` instances and display the robot GUI.
2. Load the pretrained `yolov8n.pt` weights.
3. Open the default camera using `cv2.VideoCapture(0)`.
4. Read video frames continuously and perform YOLOv8n detection.
5. Call `check_proximity_p2(results, robot)` to determine whether a P2 warning should be requested.
6. Draw detection annotations using `results[0].plot()` and display the camera view using `cv2.imshow()`.

Press **`q` in the OpenCV camera window** to exit the video-processing loop. The code should then release camera resources using `cap.release()` and `cv2.destroyAllWindows()`. **This does not necessarily close the separate PyQt6 GUI window.**

## 6. How P2 Proximity Detection Works

The camera module first runs YOLO inference:

```python
results = model.predict(source=frame, imgsz=320, conf=0.25, verbose=False)
```

- `source=frame`: Passes the current camera frame to the model.
- `imgsz=320`: Sets the model's target inference image size, not the camera's original resolution.
- `conf=0.25`: Sets the confidence threshold for retaining detections.
- `verbose=False`: Reduces detailed console output.

The proximity check compares a detection's bounding-box height with the height of the original image:

```python
box_height = y2 - y1
screen_height = results[0].orig_img.shape[0]
height_ratio = box_height / screen_height

if height_ratio > 0.8:
    robot_instance.handle_trigger(1, "P2")
```

The value **`0.8` is an image-height ratio threshold**: when a detection's bounding box occupies more than 80% of the original frame height, the system requests a P2 warning. It **does not directly mean that someone is less than 0.5 metres away**. If this threshold was selected by measuring a particular camera setup, it should be described as an **empirical threshold for those test conditions**. Accurate metric distance estimation would require further calibration or an appropriate depth sensor.

> **Detection-class note:** If `check_proximity_p2()` does not filter object classes, it checks **all YOLO detection classes**, not only people. If the intended behaviour is person-only proximity detection, add `if int(box.cls[0]) != 0: continue` inside the bounding-box loop. In the standard COCO model, `person` has class ID `0`.

## 7. Priority Control and Multithreading

The core priority comparison is implemented in `voice.py`, within `handle_trigger()`:

```python
if incoming_priority < self.current_priority:
    return

self.current_priority = incoming_priority
self.interrupt_system()
```

A lower-priority request is rejected. Otherwise, the system begins a task-transition workflow. Because the current condition uses `<` rather than `<=`, **equal-priority requests are also accepted**.

Speech playback runs in a worker thread using `threading.Thread(...)`, allowing the GUI's main thread to continue processing button events. However, **using a separate thread does not guarantee that speech already playing can be stopped immediately**. In addition, some previously scheduled `QTimer.singleShot()` callbacks may still execute later. These limitations would need to be addressed to achieve more reliable preemption.

## 8. Current Limitations and Future Improvements

- **Software simulation:** The project does not include physical robot motor control, obstacle-avoidance path planning, or localization sensors.
- **Distance accuracy:** Bounding-box ratios approximate how large a detection appears in the frame; they do not directly measure distance in metres.
- **Repeated warnings:** Consecutive frames meeting the threshold may repeatedly request P2. A cooldown or edge-triggered approach could help.
- **Task interruption:** Improve speech cancellation, timer cancellation, and state checks for more reliable task switching.
- **GUI responsiveness:** The current design calls `app.processEvents()` manually while running YOLO inference synchronously, which may cause delays. A dedicated inference worker could improve responsiveness.
- **Voice inquiry:** Keyword-based matching currently supports only a limited range of expressions.

## 9. Official References and Model Attribution

- Ultralytics YOLOv8 documentation: https://docs.ultralytics.com/models/yolov8/
- Ultralytics GitHub repository: https://github.com/ultralytics/ultralytics
- Official model assets: https://github.com/ultralytics/assets/releases
- COCO dataset: https://cocodataset.org/

**Model attribution:** `yolov8n.pt` contains pretrained weights provided by Ultralytics. This project uses the model for inference and implements its own GUI, voice workflow, proximity checks, and priority-control logic. Users should comply with the applicable Ultralytics licensing terms when using or distributing the software and model.
