import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QGuiApplication


import cv2 as cv
import numpy as np
import kociemba


# Color codes:
W=0
R=1
O=2
Y=3
G=4
B=5
BK=6
COLOR_TO_FACE = {W: 'U', R: 'R', G: 'F', Y: 'D', O: 'L', B: 'B'}
instructions = [
    "Hold the cube with WHITE on top and GREEN facing you",        
    "Rotate cube down and to the right to scan RED face",
    "Rotate cube to the left to scan GREEN face",
    "Rotate cube down to scan YELLOW face",
    "Rotate cube up and to the left to scan ORANGE face",
    "Rotate cube to the left to scan BLUE face"
]
faces = ["Top (White)", "Right (Red)", "Front (Green)", "Down (Yellow)", "Left (Orange)", "Back (Blue)"]
global currentFace
currentFace = 0
global instruction_index
instruction_index = 0
global face_colors 
face_colors = ''
global cube 
cube = [[None for i in range(3)] for j in range(3)]
global solution
solution = ''
global width
global height

def classify_color(h, s, v):
    # Black 
    if v < 50:
        return BK
    
    # White 
    if s < 60 and v > 140:
        return W
    
    # Black for low saturation
    if s < 40: 
        return BK
    
    # Yellow 
    if 25 <= h <= 38:
        return Y
    
    # Orange 
    if 10 <= h <= 24:
        return O
    
    # Red 
    if h <= 9 or h >= 170:
        return R
    
    # Green 
    if 40 <= h <= 85:
        return G
    
    # Blue 
    if 90 <= h <= 130:
        return B
    
    return None


class CameraApp(QWidget):
    def __init__(self):
        global width
        global height

        super().__init__()
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        width = geometry.width()
        height = geometry.height()
        
        self.resize(width, height)
        self.setWindowTitle("Rubik's Cube Solver")

        # UI
        self.box = QLabel(self)
        self.box.setGeometry(60,90, round(width*0.6)+20, round(height*0.55)+20)
        self.box.setStyleSheet("""background-color: rgb(0,0,0); border: 2px solid rgb(8, 117, 75);border-radius: 20px;""")

        self.image_label = QLabel(self)
        self.image_label.move(70, 100)  
        self.image_label.resize(round(width*0.6), round(height*0.55))        

        self.text_label = QLabel("Instructions: Press SPACE to record face colors.\nPress S to solve the cube. Press R to reset. Press C to clear re-scan current face", self)
        self.text_label.move(70, 30)
        self.text_label.setStyleSheet("color: white; font-size: 20px;")

        self.text_instructions = QLabel(instructions[instruction_index], self)
        self.text_instructions.move(70,  round(height*0.55) + 130)
        self.text_instructions.setStyleSheet("color: white; font-size: 20px;")

        self.solution_text = QLabel("                                                                                                                       ", self)
        self.solution_text.move(70,  round(height*0.55) + 180)
        self.solution_text.setStyleSheet("color: white; font-size: 20px;")

        self.checkboxes = []
        for i, face in enumerate(faces):
            label = QLabel(face, self)
            label.move(round(width*0.6) + 200, 100 + i*80)
            label.setStyleSheet("color: white; font-size: 20px;")

            checkbox = QLabel(self)
            checkbox.setGeometry(round(width*0.6) + 150, 95 + i*80, 40, 40)
            self.checkboxes.append(checkbox)
                    

        self.setStyleSheet("background-color: rgb(30, 30, 31);")

        # OpenCV camera
        self.cap = cv2.VideoCapture(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def keyPressEvent(self, event):
        global face_colors
        global cube
        global instruction_index
        global solution
        global currentFace

        if event.key() == Qt.Key.Key_Escape:  # Press ESC to close
            self.close()

        if event.key() == Qt.Key.Key_Space:
                    for i in range(3):
                        for j in range(3):
                            if cube[i][j] == W:
                                face_colors += 'U'
                            elif cube[i][j] == R:
                                face_colors += 'R'
                            elif cube[i][j] == O:
                                face_colors += 'L'
                            elif cube[i][j] == Y:
                                face_colors += 'D'
                            elif cube[i][j] == G:
                                face_colors += 'F'
                            elif cube[i][j] == B:
                                face_colors += 'B'
                    print("Face colors:", face_colors)
                    if instruction_index < 5:
                        instruction_index +=1
                    self.text_instructions.setText(instructions[instruction_index]) 
                    currentFace += 1
                    self.update_checkboxes()
        if event.key() == Qt.Key.Key_S:
                    try:
                        solution = kociemba.solve(face_colors)
                        print("Solution:", solution)
                    except Exception as e:
                        print("Error solving cube:", e)
                    self.solution_text.setText(f"Solution: {solution}")
        if event.key() == Qt.Key.Key_R:
                    face_colors = ''
                    cube = [[None for i in range(3)] for j in range(3)]   
                    instruction_index = 0
                    self.text_instructions.setText(instructions[instruction_index])  
                    currentFace = 0

        # if event.key() == Qt.Key.Key_C:     

    def update_frame(self):
        global width
        global height
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv.resize(frame, (round(width*0.6), round(height*0.75)))

        means = []
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        start_x = cx - 240 // 2
        start_y = cy - 240 // 2
        
        cv.rectangle(frame,(cx - 120, cy - 120),(cx + 120, cy + 120),(8, 117, 75),2)
       

        for i in range (3):
            for j in range (3):
                x=start_x + j*80 
                y=start_y + i*80

                if j < 2:
                    cv.line(frame, (x + 80, start_y), (x + 80, start_y + 240), (8, 117, 75), 1)
                if i < 2:
                    cv.line(frame, (start_x, y + 80), (start_x + 240, y + 80), (8, 117, 75), 1)

                mean = np.mean(hsv[y+20:y+60, x+20:x+60], axis=(0,1))
                cube[i][j] = classify_color(int(mean[0]), int(mean[1]), int(mean[2]))
                means.append(mean)

        for i in range (3):
            for j in range (3):
                x = 620 + j*30
                y = 220 + i*30
                color_code = cube[i][j]
                if color_code is not None:
                    if color_code == W:
                        color = (255, 255, 255)
                    elif color_code == R:
                        color = (0, 0, 255)
                    elif color_code == O:
                        color = (0, 165, 255)
                    elif color_code == Y:
                        color = (0, 255, 255)
                    elif color_code == G:
                        color = (0, 255, 0)
                    elif color_code == B:
                        color = (255, 0, 0)
                    else:
                        color = (0, 0, 0)
                    cv2.rectangle(frame, (x, y), (x + 30, y + 30), color, -1)

        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     
        h, w, ch = frameRGB.shape
        bytes_per_line = ch * w # number of bytes per line

        qt_image = QImage(frameRGB.data,w,h,bytes_per_line,QImage.Format.Format_RGB888) #width, height, bytes per line, format

        self.image_label.setPixmap(QPixmap.fromImage(qt_image)) #set the image to the label

    def closeEvent(self, event): #close the camera when closing the app
        self.cap.release()
        event.accept()

app = QApplication(sys.argv)
window = CameraApp()
window.showMaximized()
sys.exit(app.exec())
