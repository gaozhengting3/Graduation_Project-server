import os
import json
from faceRecognize import faceRecognize
import transferr
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['POST'])
def transfer():
    file_name = request.json["fileName"]
    courseID = request.json["course"]["courseID"]
    students = request.json["course"]["students"]
    retrain = request.json["course"]["retrain"]
    recongnize_result = transferr.faceRecognize(
        file_name, courseID, students, retrain)
    print(recongnize_result)
    return json.dumps(recongnize_result)


@app.route('/deepface', methods=['POST'])
def deepface():
    file_name = request.json["fileName"]
    recongnize_result = faceRecognize(file_name)
    print(recongnize_result)
    return json.dumps(recongnize_result)


@app.route('/test', methods=['POST'])
def test():
    return "Hello"


if __name__ == '__main__':
    # attendance_records_path = C:\workspace\server\public\static\attendance_records
    attendance_records_path = os.path.join(
        os.getcwd(), "public", "static", "attendance_records")
    if not os.path.exists(attendance_records_path):
        os.makedirs(attendance_records_path)
    app.run(host='0.0.0.0', port=8001, debug=True)
