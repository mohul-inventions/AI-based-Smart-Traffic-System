import cv2
import time
from ultralytics import YOLO

# ==========================================
# 1. INITIALIZATION
# ==========================================
model = YOLO("yolov8n.pt")

cap1 = cv2.VideoCapture("road1.mp4") # Heavy Traffic
cap2 = cv2.VideoCapture("road2.mp4") # Light Traffic

vehicle_classes = ["car", "motorcycle", "bus", "truck", "bicycle"]

# ==========================================
# 2. TIMING & SYSTEM VARIABLES
# ==========================================
DECISION_INTERVAL = 10  
MAX_WAIT_TIME = 120     

current_green = 1       
last_decision_time = time.time()
last_switch_time = time.time()

ambulance_mode = False  

accident_video_playing = False
accident_road1 = False   
crash_video_start_time = 0

# ⏱️ ADJUST THIS: How many seconds into road4.mp4 does the crash happen?
CRASH_DELAY_SECONDS = 44.0  

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    # Loop videos
    if not ret1:
        cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret1, frame1 = cap1.read()
    if not ret2:
        cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret2, frame2 = cap2.read()

    current_time = time.time()

    # ==========================================
    # 3. AUTOMATED ACCIDENT DETECTION SYNC
    # ==========================================
    if accident_video_playing and not accident_road1:
        if (current_time - crash_video_start_time) >= CRASH_DELAY_SECONDS:
            accident_road1 = True
            print("💥 IMPACT DETECTED! Locking down Road 1!")

    # ==========================================
    # 4. CAMERA 1 PROCESSING (Road 1 Heavy / Road 4 Accident)
    # ==========================================
    counts1 = [0]
    if ret1:
        results1 = model(frame1)
        for r in results1:
            for box in r.boxes:
                cls = int(box.cls[0])
                if model.names[cls] in vehicle_classes:
                    counts1[0] += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Box color turns RED only AFTER the crash happens
                    box_color1 = (0, 0, 255) if accident_road1 else (0, 255, 0)
                    cv2.rectangle(frame1, (x1, y1), (x2, y2), box_color1, 2)

    # ==========================================
    # 5. CAMERA 2 PROCESSING (Road 2 Light / Road 3 Ambulance)
    # ==========================================
    counts2 = [0]
    if ret2:
        results2 = model(frame2)
        valid_boxes = []
        largest_area = 0
        largest_box_idx = -1
        
        # Step 1: Find all vehicles and identify the largest one
        for r in results2:
            for box in r.boxes:
                cls = int(box.cls[0])
                if model.names[cls] in vehicle_classes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)
                    valid_boxes.append((x1, y1, x2, y2))
                    
                    # Track which box is the biggest
                    if area > largest_area:
                        largest_area = area
                        largest_box_idx = len(valid_boxes) - 1
        
        counts2[0] = len(valid_boxes)
        
        # Step 2: Draw the boxes
        for i, (x1, y1, x2, y2) in enumerate(valid_boxes):
            # If ambulance mode is ON, only the LARGEST vehicle gets the Cyan tag
            if ambulance_mode and i == largest_box_idx:
                cv2.rectangle(frame2, (x1, y1), (x2, y2), (255, 255, 0), 4)
                cv2.putText(frame2, "AMBULANCE", (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 0), 2)
            # All other vehicles get standard green boxes
            else:
                cv2.rectangle(frame2, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # ==========================================
    # 6. DECISION LOGIC (The "Brain")
    # ==========================================
    time_since_decision = current_time - last_decision_time
    time_since_switch = current_time - last_switch_time

    new_green = current_green 

    # ⚠️ Priority 1: ACCIDENT OVERRIDE (Only active after the timer hits)
    if accident_road1:
        new_green = 2  
        last_decision_time = current_time
        
    # 🚨 Priority 2: AMBULANCE OVERRIDE 
    elif ambulance_mode:
        new_green = 2
        last_decision_time = current_time 
    
    # ⏱️ Priority 3: NORMAL AI CHECKS 
    elif time_since_decision >= DECISION_INTERVAL:
        if time_since_switch >= MAX_WAIT_TIME:
            new_green = 2 if current_green == 1 else 1 
        else:
            if counts1[0] > counts2[0]:
                new_green = 1
            elif counts2[0] > counts1[0]:
                new_green = 2
        last_decision_time = current_time

    if new_green != current_green:
        last_switch_time = current_time
        current_green = new_green

    sig1 = "GREEN" if current_green == 1 else "RED"
    sig2 = "GREEN" if current_green == 2 else "RED"

    # ==========================================
    # 7. ON-SCREEN DISPLAY (UI)
    # ==========================================
    current_wait = int(current_time - last_switch_time)

    # ROAD 1 UI
    if ret1:
        color1 = (0, 255, 0) if sig1 == "GREEN" else (0, 0, 255)
        cv2.putText(frame1, f"Road 1: {sig1} ({counts1[0]})", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color1, 3)
        cv2.putText(frame1, f"Wait: {current_wait}s", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if accident_road1:
            if int(current_time * 2) % 2 == 0:
                cv2.putText(frame1, "⚠️ ACCIDENT DETECTED! HALTING TRAFFIC ⚠️", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 3)

    # ROAD 2 UI
    if ret2:
        color2 = (0, 255, 0) if sig2 == "GREEN" else (0, 0, 255)
        cv2.putText(frame2, f"Road 2: {sig2} ({counts2[0]})", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color2, 3)
        cv2.putText(frame2, f"Wait: {current_wait}s", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if ambulance_mode:
            if int(current_time * 2) % 2 == 0:
                cv2.putText(frame2, "🚨 AMBULANCE DETECTED! OVERRIDE 🚨", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 3)

    if ret1 and ret2:
        frame1 = cv2.resize(frame1, (640, 480))
        frame2 = cv2.resize(frame2, (640, 480))
        output = cv2.hconcat([frame1, frame2])
        cv2.imshow("Full Smart City ITMS Simulation", output)
    
    # ==========================================
    # 8. KEYBOARD CONTROLS
    # ==========================================
    key = cv2.waitKey(1) & 0xFF
    if key == 27: 
        break
    
    # --- TRIGGER ACCIDENT ---
    elif key == ord('x') and not accident_video_playing:
        accident_video_playing = True
        accident_road1 = False 
        crash_video_start_time = time.time() # START THE SYNC TIMER
        ambulance_mode = False 
        cap1.release()
        cap1 = cv2.VideoCapture("road4.mp4") 
        print(f"Video swapped to road4. Waiting {CRASH_DELAY_SECONDS} seconds for impact...")

    # --- TRIGGER AMBULANCE ---
    elif key == ord('a') and not ambulance_mode: 
        ambulance_mode = True
        accident_video_playing = False
        accident_road1 = False 
        cap2.release() 
        cap2 = cv2.VideoCapture("road3.mp4") 
        print("🚨 SIREN: Injecting ambulance footage!")
    
    # --- CLEAR ALL ---
    elif key == ord('c'): 
        print("✅ CLEAR: Returning to normal AI flow.")
        if accident_video_playing:
            accident_video_playing = False
            accident_road1 = False
            cap1.release()
            cap1 = cv2.VideoCapture("road1.mp4") 
        if ambulance_mode:
            ambulance_mode = False
            cap2.release() 
            cap2 = cv2.VideoCapture("road2.mp4") 

cap1.release()
cap2.release()
cv2.destroyAllWindows()

