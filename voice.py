import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
import pyttsx3
import speech_recognition as sr



class LeedsStationRobot(QWidget):

    def __init__(self):
        super().__init__()
        self.state = "IDLE"
        self.current_priority = -1
        self.speech_id = 0
        self.recognizer = sr.Recognizer()
        self.p3_timer_objects = []
        self.nav_target = ""

        self.init_ui()
        QTimer.singleShot(2000, self.delayed_start)

    def init_ui(self):
        self.setWindowTitle("Leeds Station Service Robot")
        self.setFixedSize(450, 620)
        self.setStyleSheet("QWidget { background-color: #2C3E50; color: white; font-family: 'Segoe UI', Arial; }")

        layout = QVBoxLayout()
        self.status_label = QLabel("Initializing System...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #F1C40F; font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(self.status_label)

        # Buttons with Priority Tags；
        self.btn_p0 = QPushButton("🔴 P0: Emergency Call")
        self.btn_p0.clicked.connect(lambda: self.handle_trigger(3, "P0"))
        layout.addWidget(self.btn_p0)

        self.btn_p1 = QPushButton("🔵 P1: Voice Inquiry")
        self.btn_p1.clicked.connect(lambda: self.handle_trigger(2, "P1"))
        layout.addWidget(self.btn_p1)

        self.btn_p2 = QPushButton("⚠️ P2: Obstacle Warning")
        self.btn_p2.clicked.connect(lambda: self.handle_trigger(1, "P2"))
        layout.addWidget(self.btn_p2)


        for btn in self.findChildren(QPushButton):
            btn.setStyleSheet(
                "height: 65px; border-radius: 12px; font-weight: bold; font-size: 14px; background-color: #34495E; color: white;")
        self.setLayout(layout)


    def speak(self, text, target_state):
        """Speech Engine with Global ID check for instant silencing"""
        self.speech_id += 1
        local_id = self.speech_id

        def _run():
            # Only start speaking if this thread's ID is still the most recent one
            if local_id == self.speech_id and self.state == target_state:
                # exception handing，
                try:
                    print(f">>> [{target_state}] Speaking: {text}")
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except:
                    pass

        threading.Thread(target=_run, daemon=True).start()

    def handle_trigger(self, incoming_priority, target_type):
        """Preemption Logic: Checks priority levels and enforces 2s silence"""
        if incoming_priority < self.current_priority:
            print(f"--- Blocked: {target_type} rejected due to lower priority ---")
            return

        # Immediate cleanup
        self.current_priority = incoming_priority
        self.interrupt_system()

        # 2-second Silence Phase
        if target_type == "P0":
            self.status_label.setText("Status: P0 PREEMPTING (2s Silence)")
            QTimer.singleShot(2000, self.execute_p0)
        elif target_type == "P1":
            self.status_label.setText("Status: P1 PREEMPTING (2s Silence)")
            QTimer.singleShot(2000, self.execute_p1)
        elif target_type == "P2":
            self.status_label.setText("Status: P2 PREEMPTING (2s Silence)")
            QTimer.singleShot(2000, self.execute_p2)

    # 打断P3的执行操作
    def interrupt_system(self):
        """Physically kill all logic and invalidate existing speech threads"""
        self.speech_id += 1
        self.state = "INTERRUPTING"
        for timer in self.p3_timer_objects:
            if timer.isActive(): timer.stop()
        self.p3_timer_objects.clear()

    # --- Execution Core ---

    def execute_p0(self):
        self.state = "P0"
        self.current_priority = 3
        self.status_label.setText("Status: P0 EMERGENCY")
        self.speak("Emergency signal received. Contacting control center. Staff number: 1 2 3 4 5 6.", "P0")
        QTimer.singleShot(30000, self.final_farewell)

    def execute_p1(self):
        self.state = "P1"
        self.current_priority = 2
        self.status_label.setText("Status: P1 Inquiry Active")
        self.speak("Hello, please tell me your destination. For example, light rail, bus, or pod station.", "P1")
        QTimer.singleShot(10000, self.start_p1_listen)

###YOLO & Voice
    def execute_p2(self):
        self.state = "P2"
        self.current_priority = 1
        self.status_label.setText("Status: P2 PROXIMITY WARNING")
        self.speak("Obstacle detected too close. Please maintain a safe distance of zero point five meters.", "P2")
        QTimer.singleShot(5000, self.reset_to_patrol)

    # --- Original P1 Sub-Logic (Untouched) ---

    def start_p1_listen(self):
        if self.state == "P1":
            self.status_label.setText("Status: 🔴 Listening (10s)")
            threading.Thread(target=self.recognize_thread, daemon=True).start()
            QTimer.singleShot(15000, self.p1_timeout_logic)

    # Speech-to-Text (STT)
    def recognize_thread(self):
        if self.state != "P1": return

        try:

            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.95)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                result = self.recognizer.recognize_google(audio, language='en-GB').lower()
                print(f"Recognition Result: {result}")

                # Priority check after long listening
                if self.state != "P1": return

                is_staff = any(w in result for w in ["contact", "staff", "human"])
                is_pod = any(w in result for w in ["pod", "pot"])
                is_light = any(w in result for w in ["light", "rail"])
                is_bus = any(w in result for w in ["bus", "coach"])

                if is_staff:
                    self.on_p1_success("STAFF")
                elif is_pod:
                    self.on_p1_success("Pod Station")
                elif is_light:
                    self.on_p1_success("Light Rail Station")
                elif is_bus:
                    self.on_p1_success("Bus Station")
                else:
                    self.speak("I didn't quite catch that. ", "P1")
                    QTimer.singleShot(4000, self.final_farewell)
        except:
            pass

    def on_p1_success(self, target):
        if self.state != "P1": return
        if target == "STAFF":
            self.state = "DONE_STAFF"
            self.speak("The staff contact number is 1 2 3 4 5 6.", "DONE_STAFF")
            QTimer.singleShot(10000, self.final_farewell)
        else:
            self.state = "DONE_NAV"
            self.nav_target = target
            self.status_label.setText(f"Status: Confirmed {target}")
            self.speak(f"Please follow me. Moving to {target}.", "DONE_NAV")
            QTimer.singleShot(5000, self.start_moving_process)

    def start_moving_process(self):
        if self.state != "DONE_NAV": return
        self.state = "MOVING"
        self.status_label.setText(f"Status: Moving to {self.nav_target}...")
        QTimer.singleShot(10000, self.arrive_at_target)

    def arrive_at_target(self):
        if self.state != "MOVING": return
        self.state = "ARRIVED"
        self.status_label.setText(f"Status: Arrived")
        self.speak(f"We have arrived at {self.nav_target}. Resuming patrol.", "ARRIVED")
        QTimer.singleShot(8000, self.reset_to_patrol)

    # --- P3 Patrol & Reset Logic ---

    def delayed_start(self):
        self.state = "STARTUP"
        self.current_priority = 0
        self.speak("Self-check completed. Starting operation.", "STARTUP")
        QTimer.singleShot(6000, self.reset_to_patrol)

    def reset_to_patrol(self):
        self.current_priority = 0
        self.state = "P3"
        self.status_label.setText("Status: P3 Patrolling")
        self.run_p3_cycle()

    def run_p3_cycle(self):
        """Achieve a cycle of 60 seconds, with different content broadcast every 15 seconds"""
        if self.state == "P3":
            self.speak("The robot is patrolling, please mind your surroundings.", "P3")
            t1 = QTimer(self)
            t1.setSingleShot(True)
            t1.timeout.connect(lambda: self.safe_speak("If you need emergency help, please press the red button."))
            t1.start(15000)

            t2 = QTimer(self)
            t2.setSingleShot(True)
            t2.timeout.connect(lambda: self.safe_speak("If you need guidance, please press the blue button."))
            t2.start(30000)

            t3 = QTimer(self)
            t3.setSingleShot(True)
            t3.timeout.connect(self.check_and_restart_p3)
            t3.start(60000)

            self.p3_timer_objects.extend([t1, t2, t3])

    def check_and_restart_p3(self):
        """After the 60s period expires, if it remains in P3 status, the next cycle begins."""
        if self.state == "P3":
            print("--- P3 Cycle Restarting (60s elapsed) ---")
            self.p3_timer_objects.clear()
            self.run_p3_cycle()


    def safe_speak(self, text):
        if self.state == "P3": self.speak(text, "P3")

    def p1_timeout_logic(self):
        if self.state != "P1":
            return
        self.speak("Say 'contact staff' for more help.", "P1")
        QTimer.singleShot(4000, self.final_farewell)


    def final_farewell(self):
        if self.state in ["P0", "P1", "FAREWELL", "DONE_STAFF"]:
            self.state = "FAREWELL"
            self.speak("Goodbye. Returning to patrol.", "FAREWELL")
            QTimer.singleShot(8000, self.reset_to_patrol)



if __name__ == "__main__":

    app = QApplication(sys.argv)
    robot = LeedsStationRobot()
    robot.show()
    sys.exit(app.exec())