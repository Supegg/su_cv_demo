import cv2 as cv

cap = cv.VideoCapture(0, cv.CAP_DSHOW)
width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

fourcc = cv.VideoWriter_fourcc(*"mp4v") # save cv_recording.mp4
# fourcc = cv.VideoWriter_fourcc('M','J','P','G') # save cv_recording.avi
out = cv.VideoWriter('cv_recording.mp4', fourcc, 20, (width, height))

while True:
    ret, frame = cap.read()
    if ret:
        out.write(frame)
        cv.imshow('capture', frame)
        if cv.waitKey(25) & 0xFF == ord('q'): #按键盘Q键退出
            break
    else:
        continue
cap.release()
out.release()
cv.destroyAllWindows()