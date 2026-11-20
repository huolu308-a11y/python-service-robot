import cv2
from ultralytics import YOLO
import time
import sys
from PyQt6.QtWidgets import QApplication
from voice import LeedsStationRobot

# ---------------------------------------------------------
# 1. Setup Environments
# ---------------------------------------------------------
app = QApplication(sys.argv)
robot = LeedsStationRobot()
robot.show()

model_path = "yolov8n.pt"
model = YOLO(model_path)


# ---------------------------------------------------------
# 2. Core Logic Functions
# ---------------------------------------------------------


def check_proximity_p2(results, robot_instance):
    """
    Logic A: Proximity Detection
    The linear distance is estimated by measuring the proportion of the detection box relative to the screen height.
    """

    DISTANCE_THRESHOLD_PIXEL_RATIO = 0.8


    for box in results[0].boxes:
        y1, y2 = box.xyxy[0][1], box.xyxy[0][3]
        box_height = y2 - y1
        screen_height = results[0].orig_img.shape[0]

        height_ratio = box_height / screen_height

        if height_ratio > DISTANCE_THRESHOLD_PIXEL_RATIO:
            print(f"⚠️ PROXIMITY ALERT: Object too close! Ratio: {height_ratio:.2f}")
            robot_instance.handle_trigger(1, "P2")
            return True
    return False


last_behavior_alert_time = 0
BEHAVIOR_COOLDOWN = 3


# ---------------------------------------------------------
# 3. Main Execution Loop
# ---------------------------------------------------------
cap = cv2.VideoCapture(0)


while True:
    app.processEvents()
    ret, frame = cap.read()
    if not ret:
        break


    results = model.predict(source=frame, imgsz=320, conf=0.25, verbose=False)
    proximity_flag = check_proximity_p2(results, robot)
    annotated_frame = results[0].plot()

    if proximity_flag:
        cv2.putText(annotated_frame, "TOO CLOSE! ", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    cv2.imshow("Integrated Station Robot Hub (YOLO + Voice)", annotated_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        print("Q pressed! Exiting...")
        break

# ---------------------------------------------------------
# 4. Cleanup
# ---------------------------------------------------------
cap.release()
cv2.destroyAllWindows()
print("✅ System Shutdown Gracefully.")