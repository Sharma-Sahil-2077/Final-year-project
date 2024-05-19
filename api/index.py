from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import os
import io
from PIL import Image
from flask_cors import CORS
import json 
import numpy as np
from collections import deque
import cv2
import random

app = Flask(__name__)
CORS(app)

def bfs_path(image, start, end):
    rows, cols = image.shape[:2]
    queue = deque([(start, [start])])
    visited = set()
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == end:
            return path
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited and image[nx, ny] == 255:
                queue.append(((nx, ny), path + [(nx, ny)]))
                visited.add((nx, ny))
    return None

def find_random_border_point(image, side):
    rows, cols = image.shape
    if side == 'top':
        candidates = [(0, j) for j in range(cols) if image[0, j] == 255]
    elif side == 'bottom':
        candidates = [(rows-1, j) for j in range(cols) if image[rows-1, j] == 255]
    elif side == 'left':
        candidates = [(i, 0) for i in range(rows) if image[i, 0] == 255]
    elif side == 'right':
        candidates = [(i, cols-1) for i in range(rows) if image[i, cols-1] == 255]
    if not candidates:
        return None
    return random.choice(candidates)

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
    conf_threshold = float(request.form.get('confidence', 0.10))
    mode = request.form.get('mode', 'indirect')
    try:
        # Read image data
        image_bytes = request.files['image'].read()

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Run inference
         # or 'indirect'
        wimage = np.ones_like(image) * 255  # Create a white image

        if mode == 'direct':
            X = model(image, conf=conf_threshold, classes=[2])
            for y in X:
                for mask in y.masks.xy:
                    pts = mask.astype(int).reshape((-1, 1, 2))
                    cv2.fillPoly(image, [pts], color=(255, 0, 0))  # Draw polygon
                    path = os.path.join(os.path.dirname(__file__), 'path.jpg')
                    cv2.imwrite(path, image)

        elif mode == 'indirect':
            X = model(image, conf=conf_threshold, classes=[0, 1, 3, 4])
            
            for y in X:
                for mask in y.masks.xy:
                    pts = mask.astype(int).reshape((-1, 1, 2))
                    mask_image = np.zeros_like(image)
                    cv2.fillPoly(mask_image, [pts], color=(255, 255, 255))  # Fill the polygon with white in the mask
    
                # Copy the predicted region from the original image to the white image
                    wimage[mask_image == 255] = image[mask_image == 255]
                    gray_image = cv2.cvtColor(wimage, cv2.COLOR_BGR2GRAY)
                    start = find_random_border_point(gray_image, 'top') or find_random_border_point(gray_image, 'left')
                    end = find_random_border_point(gray_image, 'bottom') or find_random_border_point(gray_image, 'right')
                    
                    if start and end:
                        path_points = bfs_path(gray_image, start, end)
                        if path_points:
                            for point in path_points:
                                wimage[point] = [0, 0, 255]  # Draw path in red
                    output_path = os.path.join(os.path.dirname(__file__), 'output.jpg')
                    cv2.imwrite(output_path, wimage)
                    
        return send_file('./output.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


if __name__ == '__main__':
    app.run(debug=True)
