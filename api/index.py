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
        print("Current position:", (x, y))
        print("Current path:", path)
        if (x, y) == end:
            print("End point reached!")
            return path
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited and image[nx, ny] == 255:
                queue.append(((nx, ny), path + [(nx, ny)]))
                visited.add((nx, ny))
                print("Added position to queue:", (nx, ny))
    print("End point not reachable.")
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



def find_red_circles(image):
    """
    Detects and returns the coordinates of red circles in the image.

    Args:
        image (numpy.ndarray): Input image in BGR format.

    Returns:
        list: List of tuples containing the coordinates of red circles.
    """
    print("Converting image to HSV color space")
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    print("Defining red color ranges in HSV")
    # Define the range for red color in HSV
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    print("Creating masks for red color")
    # Create masks for red color
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    print("Finding contours in the mask")
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centers = []
    
    print("Iterating through contours to find centers of red circles")
    # Iterate through contours and find the center of each red circle
    for contour in contours:
        print("Calculating moments of the contour")
        # Calculate the moments of the contour
        M = cv2.moments(contour)
        if M['m00'] != 0:
            # Calculate the center of the contour
            cX = int(M['m10'] / M['m00'])
            cY = int(M['m01'] / M['m00'])
            print(f"Found red circle at: ({cX}, {cY})")
            centers.append((cX, cY))
    
    print("Returning list of centers")
    return centers

def get_two_red_circle_coordinates(image):
    """
    Finds and returns the coordinates of two red circles in the image.

    Args:
        image (numpy.ndarray): Input image in BGR format.

    Returns:
        tuple: Coordinates of the first and second red circles, or None if less than two circles are found.
    """
    print("Calling find_red_circles to get red circle coordinates")
    red_circles = find_red_circles(image)
    
    print("Checking if at least two red circles are found")
    # Check if at least two red circles are found
    if len(red_circles) >= 2:
        print(f"Two red circles found at: {red_circles[0]}, {red_circles[1]}")
        return red_circles[0], red_circles[1]
    else:
        print("Less than two red circles found")
        return None



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
        image_bytes2 = request.files['image2'].read()

        nparr2 = np.frombuffer(image_bytes2, np.uint8)
        image2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)
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
                    coordinates = get_two_red_circle_coordinates(image2)
                    print(f'coordinates',coordinates[0],coordinates[1])
                    
                    path_points = bfs_path(gray_image, coordinates[0], coordinates[1])
                    print(f'bfs point',path_points)
                    if path_points:
                        for point in path_points:
                            print('executing')
                            wimage[point] = [0, 0, 255]  # Draw path in red
                    output_path = os.path.join(os.path.dirname(__file__), 'output.jpg')
                    cv2.imwrite(output_path, wimage)
                    
        return send_file('./output.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


if __name__ == '__main__':
    app.run(debug=True)
