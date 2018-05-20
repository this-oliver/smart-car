"""
<Description>
This code stream live video from the Raspberry pi 3, using the static IP address 192.168.1.200
to run this from the RPi just type: python3 run_camera.py in the RPi terminal.
To watch the live video just put the IP address on your browser and the port which it's: 8888 
finally, it will look like http://192.168.1.200:8888
</Description>

<Author>
M Nazeeh Alhosary
</Author>
Sources:
https://randomnerdtutorials.com/video-streaming-with-raspberry-pi-camera/

"""

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import serial

PAGE="""\
<html>
<head>
<title> Group 1 | Streaming </title>
</head>
<body>
<center><h1> Group 1 | Streaming </h1></center>
<center><img src="stream.mjpg" width="1080" height="720"></center>
<center><h3><cite> By M Nazeeh Alhosary </cite></h3></center>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
			 #self.send_response(200)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

arduinoSerialData = serial.Serial("/dev/serial/by-id/usb-Arduino_Srl_Arduino_Mega_75435353038351F06192-if00",9600)
#where we tell the car to do stuff
while (True):
    print("Options:")
    print("w Forward")
    print("a Left")
    print("d Right")
    print("s Backward")
    print("p Park")
    serialCommand = input("Serial Variable: ")
    arduinoSerialData.write(serialCommand.encode())


with picamera.PiCamera(resolution='1080x720', framerate=30) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = 180
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8888)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()