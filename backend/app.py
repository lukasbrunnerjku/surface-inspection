from flask import Flask, jsonify
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)  # Allow frontend requests


@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Open a browser and visit: http://localhost:5000/api/data to
    see the json response!
    """
    # Load the image and encode it in base64
    image_path = r"C:\Users\lbrunn\projects\surface-inspection\images\wood\0055.png"  # Ensure this image exists
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404

    data = {
        "text": "Hello from Flask Backend!",
        "image_base64": f"data:image/jpeg;base64,{encoded_image}"
    }
    return jsonify(data)


if __name__ == '__main__':
    """
    cd backend

    flask run

    The "flask run" will use the app.py code in the current directory.
    """
    app.run(debug=True)
