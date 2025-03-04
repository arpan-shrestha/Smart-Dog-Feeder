import RPi.GPIO as GPIO
import time
import os
import cv2
import subprocess
from ultralytics import YOLO
import serial

TRIG = 23  
ECHO = 24  
SERVO = 17  
TRIG2 = 27  # Second ultrasonic sensor for food level
ECHO2 = 22  

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SERVO, GPIO.OUT)

GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

servo = GPIO.PWM(SERVO, 50)
servo.start(0)

os.environ["QT_QPA_PLATFORM"] = "xcb"
model = YOLO("yolov8n.pt")

gsm = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

def send_sms(message):
    """Send an SMS using SIM900 GSM module."""
    gsm.write(b'AT+CMGF=1\r') 
    time.sleep(1)
    gsm.write(b'AT+CMGS="+xxx-xxxxxxxxxx"\r') #country code and number without -  
    time.sleep(1)
    gsm.write(message.encode() + b'\r')
    time.sleep(1)
    gsm.write(bytes([26]))  
    time.sleep(3)
    print("SMS sent:", message)

def get_distance(TRIG, ECHO):
    """Measure distance using ultrasonic sensor."""
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    timeout = start_time + 0.05

    while GPIO.input(ECHO) == 0:
        start_time = time.time()
        if start_time > timeout:
            return -1  

    stop_time = time.time()
    timeout = stop_time + 0.05

    while GPIO.input(ECHO) == 1:
        stop_time = time.time()
        if stop_time > timeout:
            return -1  

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  
    return round(distance, 2)

def set_servo_angle(angle):
    """Move the servo to a specific angle."""
    duty_cycle = (angle / 18) + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

def capture_and_detect():
    """Capture an image and run YOLO detection."""
    cmd = "libcamera-still -o dog.jpg --timeout 1000"
    process = subprocess.run(cmd, shell=True)

    if process.returncode == 0 and os.path.exists("dog.jpg"):
        results = model.predict("dog.jpg", conf=0.6)

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])  
                if cls == 16:  
                    print("Dog detected! Activating servo motor...")
                    set_servo_angle(90)
                    time.sleep(0.5)
                    set_servo_angle(50)
                    time.sleep(0.5)
                    set_servo_angle(0)
                    return

        print("No dog detected.")
    else:
        print("Error: Image capture failed. Check camera setup.")

food_low_alert_sent = False 

try:
    while True:
        distance = get_distance(TRIG, ECHO)
        print(f"Object Distance: {distance} cm")
        
        if 0 < distance <= 50:
            print("Object detected! Running YOLO detection...")
            capture_and_detect()

        food_level = get_distance(TRIG2, ECHO2)
        print(f"Food Level: {food_level} cm")

        if food_level >= 16 and not food_low_alert_sent:
            print("Food is running low! Sending SMS alert...")
            send_sms("Alert! The food level is low. Please refill the container.")
            food_low_alert_sent = True

        elif food_level < 15:
            food_low_alert_sent = False  

        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
    servo.stop()
    GPIO.cleanup()