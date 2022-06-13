import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0)

while(1):
    # get a frame
    ret, frame = cap.read()
    # print(ret)
    frame = cv.flip(frame, 1) # h-flip, like a mirror
    # show a frame
    cv.imshow("capture", frame)
    # cv.imwrite('cv_get_image.jpg', frame)
    if cv.waitKey(40) & 0xFF == ord('q'): # 24fps & quit
        break

cap.release()
cv.destroyAllWindows() 