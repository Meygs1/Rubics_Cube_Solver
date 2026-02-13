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
    "Rotate cube to the left to scan BLUE face",
    "Press S to solve the cube"
]
faces = ["Top (White)", "Right (Red)", "Front (Green)", "Down (Yellow)", "Left (Orange)", "Back (Blue)"]

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
        super().__init__()
        self.currentFace = 0
        self.instruction_index = 0
        self.face_colors = ''
        self.cube = [[None for i in range(3)] for j in range(3)]
        self.solution = ''
        self.SCANNING = 0
        self.SOLUTION = 1
        self.state = self.SCANNING
        self.solArr = []
        self.solIndex = 0
        self.face_labels = []

        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        self.width = geometry.width()
        self.height = geometry.height()
        
        self.resize(self.width, self.height)
        self.setWindowTitle("Rubik's Cube Solver")

        #--------------UI------------------
        self.box = QLabel(self)
        self.box.setGeometry(60,90, round(self.width*0.6)+20, round(self.height*0.55)+20)
        self.box.setStyleSheet("background-color: rgb(0,0,0); border: 2px solid rgb(8, 117, 75);border-radius: 20px;")

        self.image_label = QLabel(self)
        self.image_label.move(70, 100)  
        self.image_label.resize(round(self.width*0.6), round(self.height*0.55))        

        self.text_label = QLabel("Instructions: Press SPACE to record face colors.\nPress S to solve the cube. Press R to reset. Press C to clear re-scan current face", self)
        self.text_label.move(70, 30)
        self.text_label.setStyleSheet("color: white; font-size: 20px;")

        self.text_instructions = QLabel(instructions[self.instruction_index], self)
        self.text_instructions.move(70,  round(self.height*0.55) + 130)
        self.text_instructions.setStyleSheet("color: white; font-size: 20px;")

        self.checkboxes = []
        for i, face in enumerate(faces):
            label = QLabel(face, self)
            label.move(round(self.width*0.6) + 200, 100 + i*80)
            label.setStyleSheet("color: white; font-size: 20px;")
            self.face_labels.append(label)

            checkbox = QLabel(self)
            checkbox.setGeometry(round(self.width*0.6) + 150, 95 + i*80, 40, 40)
            self.checkboxes.append(checkbox)
                    

        self.setStyleSheet("background-color: rgb(30, 30, 31);")

        #----- OpenCV camera----
        self.cap = cv2.VideoCapture(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS
        self.update_checkboxes()
        #-----------------------


        #-----------UI for solution display-----------
        self.solution_image = QLabel(self)
        self.solution_image.move(70, 100)  # Position it where you want
        self.solution_image.resize(round(self.width*0.6), round(self.height*0.55))  # Size for the cube image
        self.solution_image.setScaledContents(True)  # Scale image to fit label
        self.solution_image.hide()  # Hidden until solution state
        
        self.move_text = QLabel(" ", self)
        self.move_text.move(70, round(self.height*0.55) + 130)
        self.move_text.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        self.move_text.hide()

        self.remaining_moves_text = QLabel(" ", self)
        self.remaining_moves_text.move(70, round(self.height*0.55) + 180)
        self.remaining_moves_text.setStyleSheet("color: white; font-size: 20px;")
        self.remaining_moves_text.hide()

        self.move2x_text = QLabel("2x", self)
        self.move2x_text.move(round(self.width*0.6), 120)
        self.move2x_text.setStyleSheet("color: rgb(136, 0, 22); font-size: 28px; font-weight: bold; background: transparent;")
        self.move2x_text.hide()

        self.instructionforSol_UI_text = QLabel("Use A and D keys to navigate through the solution steps. Press ESC to go back to scanning.", self)
        self.instructionforSol_UI_text.move(70,30)
        self.instructionforSol_UI_text.setStyleSheet("color: white; font-size: 20px;")
        self.instructionforSol_UI_text.hide()

        self.instruction_sol_text = QLabel("Hold the cube with WHITE on top and GREEN facing you", self)
        self.instruction_sol_text.move(70, round(self.height*0.55) + 230)
        self.instruction_sol_text.setStyleSheet("color: white; font-size: 20px;")
        self.instruction_sol_text.hide()

        self.progressbar = QLabel(self)
        self.progressbar.setGeometry(70, round(self.height*0.55) + 280, round(self.width*0.6), 30)
        self.progressbar.setStyleSheet("background-color: rgb(0,0,0); border: 2px solid rgb(8, 117, 75); border-radius: 5px;")
        self.progressbar.hide()

        self.progress_fill = QLabel(self)
        self.progress_fill.setGeometry(70, round(self.height*0.55) + 280, 0, 30)
        self.progress_fill.setStyleSheet("background-color: rgb(79, 244, 121); border-radius: 5px;")
        self.progress_fill.hide()
        #--------------------------------------------
    def remaining_moves(self):
        remaining = len(self.solArr) - self.solIndex - 1
        self.remaining_moves_text.setText(f"Move {self.solIndex + 1} of {len(self.solArr)}")
        self.remaining_moves_text.adjustSize()

    def update_checkboxes(self):
        for i, checkbox in enumerate(self.checkboxes):
            if self.currentFace == i: #current face being scanned
                checkbox.setStyleSheet("background-color: rgb(36, 186, 248); border: 2px solid rgb(8, 117, 75); border-radius: 5px;")
            elif self.currentFace > i: #already scanned faces
                checkbox.setStyleSheet("background-color: rgb(79, 244, 121); border: 2px solid rgb(8, 117, 75); border-radius: 5px;")
            else: #faces yet to be scanned
                checkbox.setStyleSheet("background-color: rgb(0,0,0); border: 2px solid rgb(8, 117, 75); border-radius: 5px;")
    
    def switch_to_solution(self):  
        # Hide scanning UI
        self.image_label.hide()
        self.text_label.hide()
        self.text_instructions.hide()

        for checkbox in self.checkboxes:
            checkbox.hide()
        for label in self.face_labels:  
            label.hide()
        
        # Show solution UI
        self.solution_image.show()
        self.move_text.show()
        self.remaining_moves_text.show()
        self.move2x_text.show()
        self.instructionforSol_UI_text.show()
        self.instruction_sol_text.show()
        self.progressbar.show()
        self.progress_fill.show()

    def switch_to_scanning(self):  
        # Show scanning UI
        self.image_label.show()
        self.text_label.show()
        self.text_instructions.show()

        for checkbox in self.checkboxes:
            checkbox.show()
        for label in self.face_labels:  
            label.show()
        
        # Hide solution UI
        self.solution_image.hide()
        self.move_text.hide()
        self.move2x_text.hide()
        self.solIndex = 0
        self.remaining_moves_text.hide()
        self.instructionforSol_UI_text.hide()
        self.instruction_sol_text.hide()        
        self.progressbar.hide()
        self.progress_fill.hide()

    def progress_bar(self):
        if self.solIndex < len(self.solArr):
            self.update_solution_progress()

    def update_solution_progress(self):
        total_moves = len(self.solArr)
        if total_moves >= 0:
            progress_width = int((self.solIndex + 1) / total_moves * round(self.width*0.6))
            self.progress_fill.setGeometry(70, round(self.height*0.55) + 280, progress_width, 30)
#70, round(height*0.55) + 280, round(width*0.6), 30
    
    def keyPressEvent(self, event):
#-------------Scanning state key events-------------
        if self.state == self.SCANNING:
            if event.key() == Qt.Key.Key_Escape:  # Press ESC to close
                self.close()

            if event.key() == Qt.Key.Key_Space:
                    if self.currentFace < 6:
                        for i in range(3):
                            for j in range(3):
                                if self.cube[i][j] == W:
                                    self.face_colors += 'U'
                                elif self.cube[i][j] == R:
                                    self.face_colors += 'R'
                                elif self.cube[i][j] == O:
                                    self.face_colors += 'L'
                                elif self.cube[i][j] == Y:
                                    self.face_colors += 'D'
                                elif self.cube[i][j] == G:
                                    self.face_colors += 'F'
                                elif self.cube[i][j] == B:
                                    self.face_colors += 'B'
                                else:
                                    self.face_colors += 'X'  # Unrecognized color
                        self.currentFace += 1
                        
                    if self.instruction_index < 6:
                        self.instruction_index += 1
                        self.text_instructions.setText(instructions[self.instruction_index])
                        self.text_instructions.adjustSize()
                    self.update_checkboxes()

            if event.key() == Qt.Key.Key_S:
                        if len(self.face_colors) == 54:
                            solution = ""
                            try:
                                solution = kociemba.solve(self.face_colors)
                                self.solArr = solution.split()
                                self.solIndex = 0
                                self.state = self.SOLUTION
                                self.switch_to_solution()
                                self.display_current_solution_step()
                                self.update_solution_progress()
                            except Exception as e:
                                print("Error solving cube:", e)
                            self.remaining_moves()
            if event.key() == Qt.Key.Key_R:
                        self.face_colors = ''
                        self.cube = [[None for i in range(3)] for j in range(3)]   
                        self.instruction_index = 0
                        self.text_instructions.setText(instructions[self.instruction_index])  
                        self.text_instructions.adjustSize()
                        self.currentFace = 0
                        self.update_checkboxes()

            if event.key() == Qt.Key.Key_C:     
                    if self.currentFace > 0:
                        self.cube = [[None for i in range(3)] for j in range(3)]                
                        self.face_colors = self.face_colors[:-(9)]
                        
                        self.currentFace -= 1  
                        
                        if self.instruction_index > 0: 
                            self.instruction_index -= 1
                            self.text_instructions.setText(instructions[self.instruction_index])
                            self.text_instructions.adjustSize()
                        
                        self.update_checkboxes()

#-------------Solution state key events-------------
        elif self.state == self.SOLUTION:
            self.setStyleSheet("background-color: rgb(30, 30, 31);")
            if event.key() == Qt.Key.Key_Escape:  # Press ESC to go back to scanning
                self.state = self.SCANNING
                self.switch_to_scanning()
                self.solIndex = 0
                
            if event.key() == Qt.Key.Key_A:
                if self.solIndex > 0:
                    self.solIndex -= 1
                    self.display_current_solution_step()
                    self.remaining_moves()
                    self.progress_bar()
            if event.key() == Qt.Key.Key_D:
                if self.solIndex < len(self.solArr) - 1:
                    self.solIndex += 1
                    self.display_current_solution_step()
                    self.remaining_moves()
                    self.progress_bar()

    def display_current_solution_step(self):
        if self.solIndex < len(self.solArr):
            current_move = self.solArr[self.solIndex]
            if (current_move.endswith("2")):
                base_move = current_move[:-1]     
                img_path = f"pics/notation/{base_move}.png"
                self.move2x_text.show()
            else:
                img_path = f"pics/notation/{current_move}.png"
                self.move2x_text.hide()
            pixmap = QPixmap(img_path)
            self.solution_image.setPixmap(pixmap)
            self.move_text.setText(f"Move: {current_move}")
            self.move_text.adjustSize()


#-------------OpenCV camera capture and processing-------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv.resize(frame, (round(self.width*0.6), round(self.height*0.75)))

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
                self.cube[i][j] = classify_color(int(mean[0]), int(mean[1]), int(mean[2]))
                means.append(mean)

        for i in range (3):
            for j in range (3):
                x = 620 + j*30
                y = 220 + i*30
                color_code = self.cube[i][j]
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
#close the app properly
app = QApplication(sys.argv)
window = CameraApp()
window.showMaximized()
sys.exit(app.exec())
