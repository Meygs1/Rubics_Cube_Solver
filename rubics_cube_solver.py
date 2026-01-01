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
face_colors = ''

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


capture = cv.VideoCapture(1)

while True:
    ret, frame = capture.read()
    if not ret:
        break
    frame = cv.resize(frame, (640, 480))
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Draw scan box
    cv.rectangle(frame, (200,120), (440,360), (8, 117, 75), 2)
    means = []
    
    cube = [[None for i in range(3)] for j in range(3)]

    for i in range (3):
        for j in range (3):
            x=200 + j*80 
            y=120 + i*80

            if j < 2:
                cv.line(frame, (x + 80, 120), (x + 80, 360), (8, 117, 75), 1)
            if i < 2:
                cv.line(frame, (200, y + 80), (440, y + 80), (8, 117, 75), 1)

            mean =  np.mean(hsv[y+20:y+60, x+20:x+60], axis=(0,1))
            cube[i][j] = classify_color(int(mean[0]), int(mean[1]), int(mean[2]))
            means.append(mean)

            # print(f"Square ({i},{j}) HSV: {mean[:3]}") 
            
            # print(f"Square ({i},{j}) Color Code: {cube[i][j]}")



    for i in range (3):
        for j in range (3):
            x = 520 + j*30
            y = 120 + i*30
            color_code = cube[i][j]
            if color_code == W:
                cv.rectangle(frame, (x,y), (x+30, y+30), (255,255,255), -1)
            elif color_code == R:
                cv.rectangle(frame, (x,y), (x+30, y+30), (0,0,255), -1)
            elif color_code == O:
                cv.rectangle(frame, (x,y), (x+30, y+30), (0,165,255), -1)
            elif color_code == Y:
                cv.rectangle(frame, (x,y), (x+30, y+30), (0,255,255), -1)
            elif color_code == G:
                cv.rectangle(frame, (x,y), (x+30, y+30), (0,255,0), -1)
            elif color_code == B:
                cv.rectangle(frame, (x,y), (x+30, y+30), (255,0,0), -1)
            else:
                cv.rectangle(frame, (x,y), (x+30, y+30), (0,0,0), -1)


    # cx, cy = 320, 240
    # h, s, v = hsv[cy, cx]
    # print(f"H={h}, S={s}, V={v}, Classified Color: {classify_color(h, s, v)}")

    # display = cv.flip(frame, 1)

    cv.imshow("Cube Scanner", frame)
    key = cv.waitKey(1) & 0xFF

    # EXIT if window is closed
    if cv.getWindowProperty("Cube Scanner", cv.WND_PROP_VISIBLE) < 1:
        break

    # ESC key also exits
    if key == 27:
        break

    if key == ord(' '):
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
    
    if key == ord('s'):
        try:
            solution = kociemba.solve(face_colors)
            print("Solution:", solution)
        except Exception as e:
            print("Error solving cube:", e)


capture.release()
cv.destroyAllWindows()


#To do:
#color tweaking mode
#UI
# - Capture all 6 sides
# - Map colors to kociemba notation
# - Solve cube using kociemba
# - Output solution steps
