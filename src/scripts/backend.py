import os
import json
from faceRecognize import faceRecognize
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/',methods=['POST'])
def index():
    file_name = request.json["fileName"]
    recongnize_result = faceRecognize(file_name)
    return json.dumps(recongnize_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=8001, debug=True)