#!/usr/bin/env python
from flask import Flask, render_template, request, Response, jsonify, send_from_directory, send_file
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
def collage():
    image_files = [
        file for file in sorted(os.listdir("captures"))
        if not file.startswith("collage_")  
    ][-4:]
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
    output_path = f"collages/collage_{timestamp}.jpg"
    collage.save(output_path)

    return jsonify({"status": "success", "collagePath": output_path}), 200


# http://192.168.0.27:5000/generate_collage
@app.route('/generate_collage', methods=['POST'])
def generate_collage():
    data = request.get_json()
    collage_name = data['collageName']
    frame_name = data['frameName']

    collage_file_path = os.path.join('collages', collage_name)
    frame_file_path = os.path.join('frames', frame_name)

    try:
        collage_image = Image.open(collage_file_path)
        frame_image = Image.open(frame_file_path)

        frame_image = frame_image.resize(collage_image.size)

        # collage와 frame 이미지를 합성 (투명도 유지)
        collage_with_frame = Image.alpha_composite(collage_image.convert('RGBA'), frame_image.convert('RGBA'))

        timestamp = int(time.time())
        output_path = f'collages/collage_{timestamp}.png'

        collage_with_frame.save(output_path)

        return jsonify({'status': 'success', 'framedCollageUrl': output_path}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

# 이미지 정적 경로
# http://192.168.0.27:5000/captures
@app.route('/captures/<filename>')
def get_captures(filename):
    return send_from_directory('captures', filename)


# http://192.168.0.27:5000/collages
@app.route('/collages/<filename>')
def get_collages(filename):
    return send_from_directory('collages', filename)


# http://192.168.0.27:5000/frames
@app.route('/frames/<filename>')
def get_frames(filename):
    return send_from_directory('frames', filename)


if __name__ == '__main__':
   app.run(host='0.0.0.0', debug=True, threaded=True)

   