from math import ceil
from statistics import median, mean, mode
# 正規化


def normalize(number, times, min_score=0, max_score=100, weights=[1, 1, 1]):
    # number為要正規化的數字
    # times代表number是經過幾次統計所產生的次數
    range = max_score - min_score
    total_weights = sum(weights)
    # 取得數字在區間中所在的位置(比例)
    scale = number / (total_weights * times)
    # 將比例對應至區間內的數字
    return scale * range + min_score


# 評分(分數越高代表表現越好)
'''
計分標準
1.消失次數
2.閉眼次數
3.面相的角度
'''


def judge(frames, attendees, scale_flag=True, weights=[1, 1, 1], sensitivity=0.7, min_score=0, max_score=100, interval=0.05):
    # scale_flag 分數是否要進行正規化
    # id_list 學生的姓名清單
    # weights 每種評分標準所佔的權重[消失次數, 閉眼次數, 超出面相角度次數],預設權重為2,1,1。   註:這裡的消失視為趴下睡覺
    # sensitivity 靈敏度,在單位時間內偵測到的狀態次數如果超過這個比例,則視為狀態成立,數值在0~1之間
    # min_score 縮放後的最小分數
    # max_score 縮放後的最小分數
    # interval 嚴格程度,判斷狀態的時間單位(幾張圖片),數值在0~1之間
    '''
    宣告要回傳的dictionary
    {
        statistic: {
                    minimum: number, 
                    maximum: number, 
                    median: number,  
                    average: number, 
                    mode: number,
                    }
        scores: [
            { 
                user: string,
                score: number,
                disappearedTimes: number,
                eyesClosedTimes: number,
                overAngleTimes: number
            }
        ]
    }
    '''
    # 對 sensitivity 靈敏度進行反向，達到原始數值越高，學生越容易被視為分心的效果
    sensitivity = 1 - sensitivity
    # 對 interval 嚴格程度進行反向，達到原始數值越高，學生分心越容易被發現
    interval = 1 - interval
    resultObject = {"statistic": {}, "scores": []}
    if len(attendees) == 0:
        resultObject["statistic"]["minimum"] = 0
        resultObject["statistic"]["maximum"] = 0
        resultObject["statistic"]["median"] = 0
        resultObject["statistic"]["average"] = 0
        resultObject["statistic"]["mode"] = 0
        return resultObject
    # 單位時間內的狀態紀錄表{是否消失次數, 是否閉眼次數, 是否超出面相角度}
    # 統計狀態狀態時採取Slide Window方法，1代表偵測到狀態，0則否
    per_status = {name: {"disappeard": [],
                         "eyes_closed": [],
                         "over_angle": []} for name in attendees}
    # 初始化每個學生的三種狀態次數皆為 0 {消失次數, 閉眼次數, 超出面相角度次數}
    status_count = {name: {"disappeard": 0,
                           "eyes_closed": 0,
                           "over_angle": 0} for name in attendees}
    # 取得實際 interval
    interval = interval * 50
    # 防止幀數小於 interval
    if len(frames) < interval:
        interval = len(frames)-1
    # 取得 sensitivity 判斷狀態的閥值(無條件進位)
    threshold = ceil(interval * sensitivity)
    # 取得總共會進行統計的次數
    times = len(frames) - interval + 1
    # 可能的最高分(滿分)
    full_score = times * sum(weights)
    # 圖片的計數器
    img_count = 1
    # 處理每一張圖片
    for img in frames:
        # 處理每一位學生的狀態
        for result in img["results"]:
            # 取得學生名字
            name = result["user"]
            # 如果不是有點到名的同學資訊則跳過
            if not name in attendees:
                continue
            # 如果沒有偵測到狀態視為此人消失，狀態皆成立
            if result["result"] == None:
                per_status[name]["disappeard"].append(1)
                per_status[name]["eyes_closed"].append(1)
                per_status[name]["over_angle"].append(1)
                continue

            # 記錄此人出現
            per_status[name]["disappeard"].append(0)
            # 紀錄閉眼狀態
            if result["result"]["eyesClosed"] == True:
                per_status[name]["eyes_closed"].append(1)
            else:
                per_status[name]["eyes_closed"].append(0)
            # 紀錄是否超出面相角度
            # pitch上下15度、roll左右傾30度、yaw左右轉30度
            euler_angle = result["result"]["eulerAngle"]
            if euler_angle["pitch"] > 15 or euler_angle["pitch"] < -15 or euler_angle["roll"] > 30 or euler_angle["roll"] < -30 or euler_angle["yaw"] > 30 or euler_angle["yaw"] < -30:
                per_status[name]["over_angle"].append(1)
            else:
                per_status[name]["over_angle"].append(0)
        # 如果還沒到達統計的額度就不進行統計
        if img_count < interval:
            # 計數器加 1
            img_count += 1
        else:
            # 統計每個人狀態(採取Slide Window方法)
            for name in attendees:
                # 如果狀態維持次數超過閥值，則視為狀態成立
                if sum(per_status[name]["disappeard"]) >= threshold:
                    status_count[name]["disappeard"] += 1
                if sum(per_status[name]["eyes_closed"]) >= threshold:
                    status_count[name]["eyes_closed"] += 1
                if sum(per_status[name]["over_angle"]) >= threshold:
                    status_count[name]["over_angle"] += 1
                # pop掉最前面的狀態
                per_status[name]["disappeard"].pop(0)
                per_status[name]["eyes_closed"].pop(0)
                per_status[name]["over_angle"].pop(0)
    # 初始化每個學生的分數為滿分
    scores = {name: full_score for name in attendees}
    # 統計已確認的狀態並計分
    for name in attendees:
        # 從滿分開始扣
        scores[name] -= status_count[name]["disappeard"] * weights[0]
        scores[name] -= status_count[name]["eyes_closed"] * weights[1]
        scores[name] -= status_count[name]["over_angle"] * weights[2]
        # 四捨五入到小數點後第1位
        scores[name] = round(scores[name], 1)
    # 進行正規化
    if scale_flag == True:
        for name in attendees:
            # 將分數映射至區間內
            scores[name] = normalize(
                scores[name], times, min_score, max_score, weights)
            # 四捨五入到小數點後第1位
            scores[name] = round(scores[name], 1)
    # 紀錄分數的list(用來算統計量)
    score_list = []
    # 記錄各項資料至resultObject，同時計算統計量
    for name in attendees:
        result = {
            "user": name,
            "score": scores[name],
            "disappearedTimes": status_count[name]["disappeard"],
            "eyesClosedTimes": status_count[name]["eyes_closed"] - status_count[name]["disappeard"],
            "overAngleTimes": status_count[name]["over_angle"] - status_count[name]["disappeard"]
        }
        resultObject["scores"].append(result)
        score_list.append(scores[name])
    # 紀錄統計量(四捨五入到小數點後第1位)至resultObject
    resultObject["statistic"]["minimum"] = round(min(score_list), 1)
    resultObject["statistic"]["maximum"] = round(max(score_list), 1)
    resultObject["statistic"]["median"] = round(median(score_list), 1)
    resultObject["statistic"]["average"] = round(mean(score_list), 1)
    resultObject["statistic"]["mode"] = round(mode(score_list), 1)
    return resultObject


# Testing...
# frames = [{"results": [{"user": "hao", "result": {"eulerAngle": {
#     "pitch": 4, "roll": -5, "yaw": 0}, "eyesClosed": False}}, {"user": "yan", "result": None}]}, {"results": [{"user": "hao", "result": {"eulerAngle": {
#         "pitch": 4, "roll": -5, "yaw": 0}, "eyesClosed": False}}, {"user": "yan", "result": {"eulerAngle": {
#             "pitch": 4, "roll": -5, "yaw": 0}, "eyesClosed": False}}]}]
# id_list = "hao", "yan"
# print(judge(frames, id_list, scale_flag=True, weights=[1, 1, 1],
#             sensitivity=0.7, min_score=0, max_score=100, interval=1))
