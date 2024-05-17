from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import os
import io
from PIL import Image
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

x = os.path.join(os.path.dirname(__file__), 'best.pt')
model = YOLO(x)

@app.route('/')
def home():
    return "Welcome to your Flask application!"

@app.route('/predict', methods=['POST'])
def predict():
    print(f'request.files',request.files['image'])
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
        results = model(image, conf=conf_threshold)
        for result in results:
            # Save result image
            result.save(filename='./result.jpg')

        # Send the segmented image back to the frontend
        return send_file('./result.jpg', mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'An error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
