import os
import json
from imageStatus import get_status
from judge import judge
from roll_call import roll_call
from flask import Flask, request, abort
from flask_cors import CORS
from upload import upload

root = os.getcwd()

app = Flask(__name__)
CORS(app)
# 人臉辨識點名


@app.route('/roll-call', methods=['POST'])
def course_roll_call():
    print("[python] POST to /roll-call")
    file_name = request.json["fileName"]
    courseID = request.json["course"]["courseID"]
    id_list = request.json["course"]["students"]
    retrain_flag = request.json["course"]["retrain"]
    recongnize_result = roll_call(
        file_name, courseID, id_list, retrain_flag)
    return json.dumps(recongnize_result)

# 取得學生上課狀態


@app.route('/detect', methods=['POST'])
def detect():
    print("[python] POST to /detect")
    dir_path = request.json["pathName"]
    frames = request.json["frames"]
    courseID = request.json["course"]["courseID"]
    id_list = request.json["course"]["students"]
    detect_mode = request.json["settings"]["detectMode"]
    late_seconds = request.json["settings"]["lateSeconds"]
    start_time = request.json["startTime"]
    images_info = get_status(dir_path, frames, start_time, courseID,
                             id_list, detect_mode, late_seconds)
    images_info["courseID"] = courseID
    return json.dumps(images_info)

# 專注力評分輔助


@app.route('/judge', methods=['POST'])
def course_judge():
    print("[python] POST to /judge")
    frames = request.json["frames"]
    print("This is request frames...")
    attendees = request.json["attendees"]
    print('='*20, attendees, '='*20)
    scale_flag = request.json["settings"]["scaleFlag"]
    weights = [request.json["settings"]["weights"]["disappeared"],
               request.json["settings"]["weights"]["eyesClosed"],
               request.json["settings"]["weights"]["overAngle"]]
    sensitivity = request.json["settings"]["sensitivity"]
    min_score = request.json["settings"]["minScore"]
    max_score = request.json["settings"]["maxScore"]
    interval = request.json["settings"]["interval"]

    return json.dumps(judge(frames, attendees, scale_flag, weights, sensitivity, min_score, max_score, interval))
# 學生上傳照片


@app.route('/video/<id>', methods=['POST'])
def user_upload(id):
    print("[python] POST to /video/<id>")
    file_name = request.json["fileName"]
    upload(id, file_name)
    return {"success": True}


if __name__ == '__main__':
    # attendance_records_path = C:\workspace\server\public\static\attendance_records
    attendance_records_path = os.path.join(
        os.getcwd(), "public", "static", "attendance_records")
    if not os.path.exists(attendance_records_path):
        os.makedirs(attendance_records_path)
    app.run(host='0.0.0.0', port=8002, debug=True)
