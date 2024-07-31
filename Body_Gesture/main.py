import pyautogui
import math
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)
mp_drawing = mp.solutions.drawing_utils

def detectPose(image, pose):

    output_image = image.copy()

    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
     
    results = pose.process(imageRGB)
   
    height, width, _ = image.shape
    
    landmarks = []
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks, connections=mp_pose.POSE_CONNECTIONS)
        
        for landmark in results.pose_landmarks.landmark:
            
            landmarks.append((int(landmark.x * width), int(landmark.y * height),
                                  (landmark.z * width)))
    return output_image, landmarks, results



def checkHandsJoined(img,results, draw=False):
    height, width, _ = img.shape

    output_img = img.copy()

    left_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * width,results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * height)
    right_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * width,results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * height)

    distance = int(math.hypot(left_wrist_landmark[0] - right_wrist_landmark[0],left_wrist_landmark[1] - right_wrist_landmark[1]))

    if distance < 130:
        hand_status = 'Hands Joined'
        color = (0, 255, 0)
        
    else:
        hand_status = 'Hands Not Joined'
        color = (0, 0, 255)

    if draw:
        cv2.putText(output_img, hand_status, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        cv2.putText(output_img, f'Distance: {distance}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        
    return output_img, hand_status

def checkLeftRight(img, results, draw=False):


    horizontal_position = None
    
    height, width, c = img.shape
    
    output_image = img.copy()
    
    left_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * width)
    right_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * width)
    
    if (right_x <= width//2 and left_x <= width//2):
        horizontal_position = 'Left'

    elif (right_x >= width//2 and left_x >= width//2):
        horizontal_position = 'Right'
    
    elif (right_x >= width//2 and left_x <= width//2):
        horizontal_position = 'Center'
        
    if draw:

        cv2.putText(output_image, horizontal_position, (5, height - 10), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
        cv2.line(output_image, (width//2, 0), (width//2, height), (255, 255, 255), 2)


    return output_image, horizontal_position

def checkJumpCrouch(img, results, MID_Y=250, draw=False):

        height, width, _ = img.shape
    
        output_image = img.copy()
        
        left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * height)
        right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * height)

        actual_mid_y = abs(right_y + left_y) // 2
        
        lower_bound = MID_Y-15
        upper_bound = MID_Y+100
        
        if (actual_mid_y < lower_bound):
            posture = 'Jumping'
        
        elif (actual_mid_y > upper_bound):
            posture = 'Crouching'
        
        else:
            posture = 'Standing'
            
        if draw:
            cv2.putText(output_image, posture, (5, height - 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
            cv2.line(output_image, (0, MID_Y),(width, MID_Y),(255, 255, 255), 2)
            
        return output_image, posture


if __name__ == '__main__':
    
    pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.6, model_complexity=1)


    cap = cv2.VideoCapture(0)
    cap.set(3,1280)
    cap.set(4,720)
    pTime = 0
    
    
    game_started = False 
    x_pos_index = 1
    y_pos_index = 1
    MID_Y = None
    counter = 0
    num_of_frames = 10




    
    while True:
        success, img = cap.read()    
        img = cv2.flip(img, 1)
        h, w, _ =  img.shape
        img = cv2.resize(img, (1280, 720))
        img, landmarks ,results = detectPose(img, pose_video)
        if landmarks:
            if game_started:
                img, horizontal_position = checkLeftRight(img, results, draw=True)
                if (horizontal_position=='Left' and x_pos_index!=0) or (horizontal_position=='Center' and x_pos_index==2):
                    pyautogui.press('left')
                    x_pos_index -= 1               

                elif (horizontal_position=='Right' and x_pos_index!=2) or (horizontal_position=='Center' and x_pos_index==0):
                    pyautogui.press('right')                    
                    x_pos_index += 1
                
            else:                
                cv2.putText(img, 'JOIN BOTH HANDS TO START THE GAME.', (5, h - 10), cv2.FONT_HERSHEY_PLAIN,
                            2, (0, 255, 0), 3)
            
            if checkHandsJoined(img, results)[1] == 'Hands Joined':

                counter += 1

                if counter == num_of_frames:
                    if not(game_started):
                        game_started = True
                        left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h)
                        right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h)
                        MID_Y = abs(right_y + left_y) // 2
                        pyautogui.click(x=1300, y=800, button='left')
                    else:
                        pyautogui.press('space')                 
                    counter = 0
            else:
                counter = 0
            
            if MID_Y:
                
                img, posture = checkJumpCrouch(img, results, MID_Y, draw=True)                
                if posture == 'Jumping' and y_pos_index == 1:
                    pyautogui.press('up')
                    y_pos_index += 1 

                elif posture == 'Crouching' and y_pos_index == 1:
                    pyautogui.press('down')
                    y_pos_index -= 1

                elif posture == 'Standing' and y_pos_index   != 1:
                    y_pos_index = 1
                    
        else:
            counter = 0

        cv2.imshow('Game', img)
        k = cv2.waitKey(1) & 0xFF
        if(k == 27):
            break
    cap.release()
    cv2.destroyAllWindows()