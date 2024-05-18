from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import os
import io
from PIL import Image
from flask_cors import CORS
import json 
import numpy as np
from collections import Counter
import cv2

app = Flask(__name__)
CORS(app)

x = os.path.join(os.path.dirname(__file__), 'best.pt')
model = YOLO(x)

@app.route('/')
def home():
    return "Welcome to your Flask application!"

@app.route('/predict', methods=['POST'])
def predict():
    # print(f'request.form',request.form)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Get confidence threshold value from request
    conf_threshold = float(request.form.get('confidence', 0.1))

    try:
        # Read image data
        image_bytes = request.files['image'].read()
        
        # Convert image bytes to PIL image
        image = Image.open(io.BytesIO(image_bytes))

        # Run inference
        results = model(image, conf=conf_threshold,show_boxes=False)
        
        for result in results:
            save_path = os.path.join(os.path.dirname(__file__), 'result.jpg')
            result.save(filename=save_path)
        
        return send_file('./result.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    
@app.route('/predict/list', methods=['POST'])
def predict_list():
    # print(f'request.form',request.form)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Get confidence threshold value from request
    conf_threshold = float(request.form.get('confidence', 0.1))

    try:
        # Read image data
        image_bytes = request.files['image'].read()
        
        # Convert image bytes to PIL image
        image = Image.open(io.BytesIO(image_bytes))

        # Run inference
        
        X = model(image, conf=conf_threshold)
        for y in X:
            k_list=y.boxes.cls.tolist() 
            print(f'k.........',k_list)

        
        return jsonify(k_list)
    
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/predict/path', methods=['POST'])
def predict_path():
    # print(f'request.form',request.form)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Get confidence threshold value from request
    conf_threshold = float(request.form.get('confidence', 0.1))

    try:
        # Read image data
        image_bytes = request.files['image'].read()

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Run inference
        X = model(image, conf=conf_threshold, classes = [0,1,3,4])
                
        for y in X:
            for mask in y.masks.xy:
                pts = mask.astype(int).reshape((-1, 1, 2))
                cv2.fillPoly(image, [pts], color=(0,255,0),)  # Draw polygon
                path=os.path.join(os.path.dirname(__file__), 'path.jpg')
                cv2.imwrite(path, image)

        return send_file('./path.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


if __name__ == '__main__':
    app.run(debug=True)
