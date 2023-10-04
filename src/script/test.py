from faceRecognize import faceRecognize
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'hello'

@app.route('/test', methods=['POST'])
def test():
    print("=========")
    data = request.json
    filename = data["filename"]
    path = os.getcwd()
    print(path)
    after = os.path.join(path, filename)
    print(after)
    print("=========")
    return ""
if __name__ == '__main__':
    app.run(port=8001, debug=True)