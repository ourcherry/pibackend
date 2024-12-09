#!/usr/bin/env python
from flask import Flask, render_template, Response, jsonify, send_from_directory
from camera import Camera
from PIL import Image
from flask_cors import CORS
import time
import os

app = Flask(__name__)

# 모든 도메인에 대해 CORS 허용
CORS(app)  

camera = Camera()

# http://192.168.0.27:5000
@app.route('/')
def index():
   return render_template('index.html')

def gen(camera):
   while True:
       frame = camera.get_frame()
       yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# http://192.168.0.27:5000/video_feed
@app.route('/video_feed')
def video_feed():
   return Response(gen(Camera()),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


# http://192.168.0.27:5000/capture
@app.route('/capture', methods=['POST'])
def capture():
    frame = camera.get_frame()
    timestamp = int(time.time())
    file_path = f"captures/capture_{timestamp}.jpg"
    with open(file_path, 'wb') as f:
        f.write(frame)
    return jsonify({"status": "success", "imagePath": file_path}), 200


# http://192.168.0.27:5000/collage
@app.route('/collage', methods=['POST'])
def create_collage():
    image_files = sorted(os.listdir("captures"))[-4:]  # 최근 4개 이미지 가져오기
    images = [Image.open(f"captures/{file}") for file in image_files]

    if len(images) < 4:
        return jsonify({"status": "error", "message": "4장의 사진이 필요합니다."}), 400

    width, height = images[0].size
    collage = Image.new('RGB', (width * 2, height * 2))

    collage.paste(images[0], (0, 0))
    collage.paste(images[1], (width, 0))
    collage.paste(images[2], (0, height))
    collage.paste(images[3], (width, height))

    timestamp = int(time.time())
    output_path = f"captures/collage_{timestamp}.jpg"
    collage.save(output_path)

    return jsonify({"status": "success", "collagePath": output_path}), 200


# 이미지 정적 경로
# http://192.168.0.27:5000/captures
@app.route('/captures/<filename>')
def get_image(filename):
    return send_from_directory('captures', filename)

if __name__ == '__main__':
   app.run(host='0.0.0.0', debug=True, threaded=True)

   