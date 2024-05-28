from flask import Flask, request,Response, jsonify, send_file
from ultralytics import YOLO
import os
import io
from PIL import Image ,ImageDraw,ImageFont
from flask_cors import CORS
import ffmpeg
import tempfile
import base64
import glob
from moviepy.editor import ImageSequenceClip

import json 
import numpy as np
from collections import deque
import cv2
from werkzeug.utils import secure_filename
import re

import heapq
import time

# Define a counter for generating unique filenames
counter = 1
app = Flask(__name__)
CORS(app)

def within_bounds(x, y, image_shape):
    return 0 <= x < image_shape[1] and 0 <= y < image_shape[0]

def euclidean_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def get_neighbors(x, y, image, image_shape):
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])
    
    neighbors = []
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            nx, ny = x + dx, y + dy
            if within_bounds(nx, ny, image_shape) and kernel[dy + 1, dx + 1] == 1:
                if np.all(image[ny+1, nx+1] == [255, 255, 255]):
                    neighbors.append((nx, ny))
    return neighbors

def dijkstra(image, start, end):
    print('function started')
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Directions for moving in 8 directions (N, S, E, W, NE, NW, SE, SW)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Distance array
    dist = np.full((height, width), np.inf)
    dist[start[1], start[0]] = 0
    
    # Priority queue for the Dijkstra's algorithm
    priority_queue = [(0, start)]
    heapq.heapify(priority_queue)

    # Dictionary to keep track of the path
    came_from = {start: None}
    print('loop started')
    while priority_queue:
        current_dist, (cx, cy) = heapq.heappop(priority_queue)
        
        if (cx, cy) == end:
            print(f"End reached at distance: {current_dist}")
            break

        for direction in directions:
            nx, ny = cx + direction[0], cy + direction[1]

            if 0 <= nx < width and 0 <= ny < height and (image[ny, nx] == 255).any():
                next_dist = current_dist + 1
                if next_dist < dist[ny, nx]:
                    dist[ny, nx] = next_dist
                    heapq.heappush(priority_queue, (next_dist, (nx, ny)))
                    came_from[(nx, ny)] = (cx, cy)

    # Trace the path back from the end to the start
    path = []
    current = end if dist[end[1], end[0]] != np.inf else None
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()

    if path and path[0] != start:
        print("No complete path found. Returning the incomplete path.")
        # Find the last point before encountering an obstacle
        for i in range(len(path) - 1, 0, -1):
            if image[path[i][1], path[i][0]] == 0:  # Check if it's an obstacle
                path = path[:i]
                break

    elif not path:
        
        print("No path found.")
    
    return path

def find_blue_circles(image):
    print('function fired')
    # Load the image
    # image = cv2.imread(image_path)
    print('image loaded')
    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range for the color blue
    lower_blue = np.array([110, 50, 50])
    upper_blue = np.array([130, 255, 255])
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


x = os.path.join(os.path.dirname(__file__), 'best.pt') # for segementation
y = os.path.join(os.path.dirname(__file__), 'larch.pt') # for detection
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

def images_to_video(images_dir, output_video_path):
    image_files = [os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.endswith('.jpg')]
    if not image_files:
        print("No images found in the directory.")
        return

    # Read the first image to get dimensions
    first_image = cv2.imread(image_files[0])
    height, width, _ = first_image.shape

    # Define codec and VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, 30, (width, height))

    # Write each image to the video
    for image_file in image_files:
        frame = cv2.imread(image_file)
        out.write(frame)

    # Release VideoWriter
    out.release()

def extract_number(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(0)) if match else -1

@app.route('/predict/video', methods=['POST'])

def predict_video():
    print("Received request to /upload.")
    if 'video' not in request.files:
        print("No video part in the request.")
        return 'No video part', 400

    file = request.files['video']
    directory = os.path.dirname('X:/Projects/tree-sense/nextjs-flask/api/resultvid/')
    print('path',os.path.dirname(__file__) )
    for filename in os.listdir(directory):
            # Check if the file starts with "frame_"
            if filename.startswith("frame_"):
                # Construct the full file path
                file_path = os.path.join(directory, filename)
                print('deleting file')
                # Delete the file
                os.remove(file_path)
            else:
                pass
    
    
    # Convert BytesIO to a numpy array
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(file.read())
        temp_video_path = temp_video.name
    
    try:
        # Open the temporary file with OpenCV
        video_capture = cv2.VideoCapture(temp_video_path)
        
        # Check if video was opened successfully
        if not video_capture.isOpened():
            return jsonify({"error": "Cannot open video"}), 400
        
        # Read the first frame
        frames_data = []

        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        print('total frames',total_frames)
        

# Iterate through files in the directory
        
        counter = 0
        for _ in range(total_frames):
            ret, frame = video_capture.read()
            if ret:
                # Convert frame to grayscale
                results = model(frame, show_boxes = False)
                for result in results:
                    
                    save_path = os.path.join('X:/Projects/tree-sense/nextjs-flask/api/resultvid' , f'frame_{counter}.jpg')

                    
                    result.save(filename=save_path)
                    counter += 1
                    print('file saved',counter)
                # Encode the grayscale frame to base64
        counter = 0
        print('counter',counter)

        image_folder = 'X:/Projects/tree-sense/nextjs-flask/api/resultvid/'
        video_name = 'video.mp4'
    
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        video = cv2.VideoWriter(video_name, fourcc, 30, (width,height))
        
        # for image in images:
        #     print('image',image)
        video_path_opencv = './video_opencv.mp4'
        video_path_moviepy = './video.mp4'

        # image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.jpg')]

        # for image_file in image_files:
        #     video.write(cv2.imread(image_file))
        # cv2.destroyAllWindows()
        # video.release()

        image_files = ([os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.jpg')])
        image_files.sort(key=lambda f: extract_number(os.path.basename(f)))
        print(image_files)
        clip = ImageSequenceClip(image_files, fps=30)

        videopath = os.path.join(os.path.dirname(__file__), 'video.mp4')
        clip.write_videofile(videopath,fps=30)
        
        # for filename in os.listdir(directory):
        #     # Check if the file starts with "frame_"
        #     if filename.startswith("frame_"):
        #         # Construct the full file path
        #       while counter <= total_frames:
        #         file_path = os.path.join(directory, f'frame_{counter}.jpg')
        #         print('file',file_path)
        #         video.write(cv2.imread(file_path))
        #     else:
        #         pass
        cv2.destroyAllWindows()
        video.release()

                # Write each image to the video
        # for image_file in image_files:
        #         print('name',image_file)
        #         frame = cv2.imread(image_file)
        #         video_writer.write(frame)
        #         print('added')
        #         # Release the video writer
        
                    
        
        # else:
        #     return jsonify({"error": "Cannot read frame from video"}), 400
        
        
    finally:
        # Release the video capture and clean up the temporary file
     
        # video_writer.release()
        video_capture.release()
        # os.remove(temp_video_path)


        
        return send_file(video_name, mimetype='video/mp4',as_attachment=True)



    # Process the video as needed
    # For example, you can display the video sin a web page
    # or perform real-time processing

    # Example: Display the video in a web page
       
    if video_capture:
        # Save the video file temporarily
        # file_path = 'temp_video.mp4'
        # file.save(file_path)

        # Initialize VideoCapture
        cap = cv2.VideoCapture(video_capture) 
        if not cap.isOpened():
            print("Error: Could not open video file.")
            return 'Error: Could not open video file.', 500

        # Get video frame dimensions
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create a directory to store result images
        result_images_dir = 'result_images'
        os.makedirs(result_images_dir, exist_ok=True)

        while cap.isOpened():
            success, frame = cap.read()
            print('frame',frame)
            counter = 1
            if success:
                # Process your frame here (e.g., model inference)
                results = model(frame)
                
                for result in results:
                    timestamp = int(time.time())  # Current timestamp
                    save_path = os.path.join('./result_images/', f'result_{timestamp}_{counter}.jpg')
                    result.save(save_path)
                    counter += 1
                    print('./result_images/', f'result_{timestamp}_{counter}.jpg')
                
                # Increment counter for the next image
                
                
                # Save the result image
                cv2.imwrite(save_path, results)

            else:
                counter = 0
                print('All frames processed.')
                break

        # Release everything when done
        cap.release()

        # Remove the temporary video file
        os.remove(file_path)

        # Merge the saved images into a video
        video_path = 'output.avi'
        images_to_video(result_images_dir, video_path)

        # Return the video file path to the frontend
        return send_file(video_path, as_attachment=True)

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
        results = model(image, conf=conf_threshold,show_boxes=False,classes=[0, 1, 3, 4])
        
        for result in results:
            save_path = os.path.join(os.path.dirname(__file__), 'result.jpg')
            result.save(filename=save_path)
        
        return send_file('./result.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    
@app.route('/path', methods=['POST'])
def predictPath():
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
        results = model(image, conf=conf_threshold,show_boxes=False, classes= 2)
        
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
    conf_threshold = float(request.form.get('confidence', 0.1))
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
        start = (start[0], start[1])  # Swap cX and cY for the start coordinate
        end = (end[0], end[1])  
        print(f'Start End', start, end)
        wimage = np.ones_like(image) * 255
        
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


                image2= Image.fromarray(image2)
                draw = ImageDraw.Draw(image2)
                print('drawww')
                point_radius = 5

                # Draw the start point as a green circle
               
                print('circles drawn')
                path = dijkstra(wimage, start, end)
                print(path)
    # Draw the path on the image
                if path:
                    print('sending')
                    draw = ImageDraw.Draw(image2)
                    for point in path:
                        draw.point(point, fill="red") 
                    
                    image_bytes = io.BytesIO()
                    image2.save(image_bytes, format='PNG')
                    image_bytes.seek(0)
                    
                    return send_file(image_bytes, mimetype='image/png')
                else:
        # Create a new image or use the existing image2
                    draw = ImageDraw.Draw(image2)
                    text = "Path not found"
                    font_size = 36

                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except IOError:
                        font = ImageFont.load_default()

                    # Calculate text size and position
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    width, height = image2.size
                    text_x = (width - text_width) // 2
                    text_y = (height - text_height) // 2

                    draw.text((text_x, text_y), text, font=font, fill="red")
                    
                    image_bytes = io.BytesIO()
                    image2.save(image_bytes, format='PNG')
                    image_bytes.seek(0)
                    
                    return send_file(image_bytes, mimetype='image/png')
                # # Draw the path on the image in batches
                # for batch_index in range(0, len(batched_path), batch_size):
                #     # Get the paths for the current batch
                #     batch_paths = batched_path[batch_index:batch_index+batch_size]
                #     images = []
                #     print('loop')
                #     # Draw paths for the current batch
                #     for paths in batch_paths:
                #         draw.line(paths, fill=(255, 255, 0), width=3)
                    
                #     # Save the image with the current batch of paths added
                #         print('saving')
                #         xpath = os.path.join(os.path.dirname(__file__), 'path.jpeg')
                #         image_pil.save(xpath)
                #         print('Image saved at:', xpath)

                #         images.append(xpath) 

                        
                #         time.sleep(5)
                #         print('interation')  # Delay between saving each image
            # return send_file('path.jpeg', mimetype='image/jpeg', as_attachment=True)
                    # Save or return the image with the path found
                    # output_path = os.path.join(os.path.dirname(__file__), 'output.jpg')
                    # cv2.imwrite(output_path, wim)
                    # return send_file('./output.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500


if __name__ == '__main__':
    app.run(debug=True)
