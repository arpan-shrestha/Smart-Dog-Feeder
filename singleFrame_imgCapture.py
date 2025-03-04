from ultralytics import YOLO
import cv2
import subprocess

model = YOLO("yolov8n.pt")
cmd = "libcamera-still -o dog.jpg --timeout 1000"
subprocess.run (cmd, shell=True)

result = model("dog.jpg")
frame = result[0].plot()
cv2.imshow("Dog Feeder", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()