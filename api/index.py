from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import os
import io
from PIL import Image ,ImageDraw
from flask_cors import CORS
import json 
import numpy as np
from collections import deque
import cv2
import random
import heapq
import time
import base64

app = Flask(__name__)
CORS(app)

def dijkstra_shortest_path(image, start, end):
    print('function firedddddddddd')
   
    # Ensure start and end points are within image bounds
    rows, cols,layers = image.shape
    print(f'Image shape: {image.shape},')
    print(rows,cols)

    if not (0 <= start[0] < rows and 0 <= start[1] < cols and 0 <= end[0] < rows and 0 <= end[1] < cols):
        return None

    # Check if start and end points are white
    if not image[start[0], start[1]].any(): 
        return None
    # Initialize distances and priority queue
    print(start,end)
    dist = {start: 0}
    pq = [(0, start)]
    prev = {start: None}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    visited = set()
    last_valid_point = start
    while pq:
        current_dist, current = heapq.heappop(pq)
        if current in visited:
            continue
        
        visited.add(current)

        if current == end:
            last_valid_point = current
            break
        for direction in directions:
            neighbor = (current[0] + direction[0], current[1] + direction[1])
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and image[neighbor[0], neighbor[1]].any():
                distance = current_dist + 1
                if neighbor not in dist or distance < dist[neighbor]:
                    dist[neighbor] = distance
                    prev[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
                    last_valid_point = neighbor

    # Reconstruct path
    path = []
    step = last_valid_point
    while step is not None:
        path.append(step)
        step = prev.get(step)
        
    path.reverse()

    # # Print the path one step at a time
    # for point in path:
    #     print(f'point',point)
    print('path',path)
    # Draw the path on the image using matplotlib
    # result_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    # print(f'result',result_image)
    # for point in path:
    #     result_image[point[0], point[1]] = [0, 0, 255]  # Red color for the path
    
    return path

def dijkstra(start, end, image):
    rows, cols, _ = image.shape
    visited = np.zeros((rows, cols), dtype=bool)
    distance = np.full((rows, cols), np.inf)
    parent = np.full((rows, cols, 2), -1, dtype=int)

    start_r, start_c = start
    end_r, end_c = end
    distance[start_r, start_c] = 0
    pq = [(0, start)]
    
    while pq:
        dist, (r, c) = heapq.heappop(pq)
        if visited[r, c]:
            continue
        visited[r, c] = True
        if (r, c) == (end_r, end_c):
            break  # Early termination if end node is reached
        
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc] and image[nr, nc] == 255:
                    new_dist = dist + np.sqrt(dr**2 + dc**2)
                    if new_dist < distance[nr, nc]:
                        distance[nr, nc] = new_dist
                        parent[nr, nc] = (r, c)
                        heapq.heappush(pq, (new_dist, (nr, nc)))
    
    path = []
    r, c = end_r, end_c
    while parent[r, c][0] != -1:
        path.append((r, c))
        r, c = parent[r, c]
    path.append((start_r, start_c))
    path.reverse()
    
    return path

def visualize_path(image, path):
    for r, c in path:
        image[r][c] = 0  # Assuming black represents the path
    output_path = os.path.join(os.path.dirname(__file__), 'output.jpg')
    cv2.imwrite(output_path, image)
    print("Path visualization saved to", output_path)

# Example usage:
# Define your image, start, and goal coordinates
# image = np.array(...)
# start = (...)
# goal = (...)
# path = astar(image, start, goal)


# Example usage:
# Define your image, start, and goal coordinates
# image = np.array(...)
# start = (...)
# goal = (...)
# path = astar(image, start, goal)



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



def find_blue_circles(image):
    print('function fired')
    # Load the image
    # image = cv2.imread(image_path)
    print('image loaded')
    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range for the color blue
    lower_blue = np.array([100, 150, 0])
    upper_blue = np.array([140, 255, 255])
    print('color stated')

    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Blur the mask to reduce noise
    blurred = cv2.GaussianBlur(mask, (9, 9), 2)

    # Detect circles using HoughCircles
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                               param1=50, param2=30, minRadius=5, maxRadius=0)
    print('circle found',circles)

    # If circles are detected, return their coordinates
    coordinates = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y,r) in circles:
            print(f'x,y',x,y,r)
            coordinates.append((x, y,r))
    print(f'coordinates',coordinates)
    return coordinates


x = os.path.join(os.path.dirname(__file__), 'best.pt')
y = os.path.join(os.path.dirname(__file__), 'larch.pt')
model = YOLO(x)
model2 = YOLO(y)
@app.route('/')
def home():
    return "Welcome to your Flask application!"

@app.route('/predict/clasify', methods=['POST'])
def detect():
    print('function started')
    # print(f'request.form',request.form)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Get confidence threshold value from request
    conf_threshold = float(request.form.get('confidence', 0.10))

    try:
        # Read image data
        

        image_bytes = request.files['image'].read()
        
        print('Image loaded')
        # Convert image bytes to PIL image
        image = Image.open(io.BytesIO(image_bytes))
        print(image)
        # Run inference
        results = model2(image, conf=conf_threshold,)
        print(results)
        for result in results:
            save_path = os.path.join(os.path.dirname(__file__), 'clasify.jpg')
            result.save(filename=save_path)
        
        return send_file('./clasify.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500

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
        results = model(image, conf=conf_threshold,show_boxes=False,classes=[0, 1,2, 3, 4])
        
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
        
        X = model(image, conf=conf_threshold,classes=[0, 1, 2, 3, 4])
        for y in X:
            k_list=y.boxes.cls.tolist() 
            print(f'k.........',k_list)

        
        return jsonify(k_list)
    
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/predict/path', methods=['POST'])
def predict_path():
    print('path')
    # print(f'request.form', request.form)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Get confidence threshold value from request
    conf_threshold = float(request.form.get('confidence', 0.01))
    mode = request.form.get('mode', 'indirect')
    try:
        # Read image data
        image_bytes = request.files['image'].read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        image_bytes2 = request.files['image2'].read()
        nparr2 = np.frombuffer(image_bytes2, np.uint8)
        image2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        # Debugging: Check shapes of images
        print(f'image shape: {image.shape}')
        print(f'image2 shape: {image2.shape}')

        # Ensure both images are 3-channel
    
          # Create a white image
        coordinates = find_blue_circles(image2)
        print(f'blueeee coordinates', coordinates[0], coordinates[1])
        print('wimageeeeeeeeeee')
            


        end = coordinates[0]
        start = coordinates[1]
        start = (start[1], start[0])  # Swap cX and cY for the start coordinate
        end = (end[1], end[0])  
        print(f'Start End', start, end)
        wimage = np.ones_like(image) * 255
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

            # Debugging: Check shape of wimage before converting to grayscale
                print(f'wimage shape before conversion: {wimage.shape}')
                gray_wimage = cv2.cvtColor(wimage, cv2.COLOR_BGR2GRAY)

                
                    # cv2.imwrite("temp_image.jpg", wimage)  # Save the numpy array as a temporary image file
                    # ximage = cv2.imread("temp_image.jpg", cv2.IMREAD_GRAYSCALE)  # Read the temporary image file
                    # os.remove("temp_image.jpg") 
                   
                    # shortest_path = dijkstra(start, end, ximage)
                    # visualize_path(ximage, shortest_path)

# Create a binary image where traversable areas are 255 and non-traversable areas are 0
                
                
                    # Now you can use binary_wimage with the dijkstra_shortest_path function
                path = dijkstra(start, end,wimage)
                # path =dijkstra(start,end,wimage)
                batch_size = len(path)
                batched_path = [path[i:i+batch_size] for i in range(0, len(path), batch_size)]
                
                # imagex = cv2.imread(image2)  # Replace 'your_image.jpg' with the path to your image
                 # Replace with your path coordinates

                # Define the batch size
                 # Adjust the batch size as needed

                image_pil = Image.fromarray(wimage)
                print('drawww')
                draw = ImageDraw.Draw(image_pil)

    # Define the radius for start and end points
                point_radius = 5

                # Draw the start point as a green circle
                draw.ellipse(
                    [(start[1] - point_radius, start[0] - point_radius), 
                    (start[1] + point_radius, start[0] + point_radius)], 
                    outline=(0, 255, 0), fill=(0, 255, 0)
                )

                # Draw the end point as a red circle
                draw.ellipse(
                    [(end[1] - point_radius, end[0] - point_radius), 
                    (end[1] + point_radius, end[0] + point_radius)], 
                    outline=(255, 0, 0), fill=(255, 0, 0)
                )

                # Draw the path on the image in batches
                for batch_index in range(0, len(batched_path), batch_size):
                    # Get the paths for the current batch
                    batch_paths = batched_path[batch_index:batch_index+batch_size]
                    images = []
                    print('loop')
                    # Draw paths for the current batch
                    for paths in batch_paths:
                        draw.line(paths, fill=(255, 255, 0), width=3)
                    
                    # Save the image with the current batch of paths added
                        print('saving')
                        xpath = os.path.join(os.path.dirname(__file__), 'path.jpeg')
                        image_pil.save(xpath)
                        print('Image saved at:', xpath)

                        images.append(xpath) 

                        
                        time.sleep(5)
                        print('interation')  # Delay between saving each image
                    return send_file('path.jpeg', mimetype='image/jpeg', as_attachment=True)
                    # Save or return the image with the path found
                    # output_path = os.path.join(os.path.dirname(__file__), 'output.jpg')
                    # cv2.imwrite(output_path, wim)
                    # return send_file('./output.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


if __name__ == '__main__':
    app.run(debug=True)
