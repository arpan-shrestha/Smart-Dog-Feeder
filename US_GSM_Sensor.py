import serial
import time
import RPi.GPIO as GPIO 

TRIG = 23  
ECHO = 24  

GPIO.setmode(GPIO.BCM)  
GPIO.setup(TRIG, GPIO.OUT)  
GPIO.setup(ECHO, GPIO.IN)  

ser = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

def send_at(command, delay=1):
    """Send AT command and return response (handles decoding errors)."""
    ser.write((command + "\r\n").encode())  
    time.sleep(delay)  
    response = ser.read(ser.inWaiting()).decode(errors='ignore')  
    print(f"> {command}") 
    print(f"< {response}")  
    return response

def measure_distance():
    """Measure distance using HC-SR04 ultrasonic sensor."""
    GPIO.output(TRIG, True)  
    time.sleep(0.00001) 
    GPIO.output(TRIG, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    while GPIO.input(ECHO) == 1:
        stop_time = time.time()


    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2  
    return round(distance, 2)  


ser.flush()

print("✅ Checking GSM module...")
if "OK" in send_at("AT"):  
    print("✅ GSM module is working!")
else:
    print("❌ No response from GSM module. Check connections.")


print("✅ Setting SMS mode...")
send_at("AT+CMGF=1")  

phone_number = "+977xxxxxxxxxx"  
message = "Alert! Object detected within 100 cm!"

print("📡 Monitoring distance...")
try:
    while True:
        distance = measure_distance()
        print(f"📏 Distance: {distance} cm")
        
        if distance <= 100: 
            print(f"🚨 Object detected at {distance} cm! Sending SMS...")
            send_at(f'AT+CMGS="{phone_number}"') 
            time.sleep(1)
            ser.write((message + "\x1A").encode())  
            time.sleep(3)
            print("✅ SMS Sent!")

        time.sleep(2)  

except KeyboardInterrupt:
    print("🔴 Stopping program...")
    GPIO.cleanup() 
    ser.close()


