from imutils import face_utils
import numpy as np
import dlib
import cv2
from PIL import Image
import colorsys
import xgboost as xgb
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from django.conf import settings
import pickle

path = '/var/www/models'
predictor = dlib.shape_predictor(path+"/shape_predictor_68_face_landmarks.dat")
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(path+'/shape_predictor_5_face_landmarks.dat')

def align_faces(img):
    dets = detector(img, 1)
    if len(dets) == 0:
        return None
    objs = dlib.full_object_detections()
    for detection in dets:
        s = sp(img, detection)
        objs.append(s)
        
    faces = dlib.get_face_chips(img, objs, size=256, padding=0.35)
    
    return faces

################### XGBoost Model ########################
# load
xgb_model = pickle.load((open(path+'/xgb_model.pkl', "rb")))

###########################################

# 얼굴에서 가져온 RGB값으로 그래프 그리기

def cv_imread(file_path):
    cv_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
    return cv_img

def face_color(frame):
    img = Image.open(frame)
    
    fr0 = cv_imread(frame)
    if max(fr0.shape) > 1500:
        fr0= cv2.resize(fr0, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    fr1 = cv2.cvtColor(fr0, cv2.COLOR_BGR2RGB)
    fr = align_faces(fr1)
    if fr == None:
        return None
    else:
        fr = fr[0]
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)    

        rects = detector(gray, 0)
        if len(rects) != 1:
            return None
        for k, d in enumerate(rects):
            shape = predictor(gray, d)
            shape = face_utils.shape_to_np(shape)
#        for (x, y) in shape:
#            cv2.circle(fr, (x, y), 2, (0, 255, 0), -1)

        point1 = ((shape[57] + shape[8]) * 0.5).round()  # point1 턱 (밑입술 하단 - 턱끝 )
    # point2 왼쪽 뺨 (왼쪽 외곽선 - 왼쪽 입술 끝점)
        point2 = ((shape[2] + shape[48]) * 0.5).round()
    # point3 오른쪽 뺨 (오른쪽 외곽선 - 오른쪽 입술 끝점)
        point3 = ((shape[14] + shape[54]) * 0.5).round()
        point4 = shape[29].astype('float64')  # point4 코
        point5 = ((shape[21] + shape[22]) * 0.5).round()  # point5 눈썹 사이
    # RGB 모드로 변경
        fro = Image.fromarray(fr)
        rgb_img = fro.convert('RGB')
    #fr = Image.fromarray(fr)
    # 지정한 좌표의 색상을 r,g,b 변수에 넣음
        r1, g1, b1 = rgb_img.getpixel((point1[0], point1[1]))
        r2, g2, b2 = rgb_img.getpixel((point2[0], point2[1]))
        r3, g3, b3 = rgb_img.getpixel((point3[0], point3[1]))
        r4, g4, b4 = rgb_img.getpixel((point4[0], point4[1]))
        r5, g5, b5 = rgb_img.getpixel((point5[0], point5[1]))
        rgb = np.array([[r1, g1, b1], [r2, g2, b2], [
                   r3, g3, b3], [r4, g4, b4], [r5, g5, b5]])

    # 그래프 그리기
        bar = np.zeros((50, 300, 3), dtype="uint8")
        startX = 0

        hist = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        centroids = rgb

        for (percent, color) in zip(hist, centroids):
            endX = startX + (percent * 300)
            cv2.rectangle(bar, (int(startX), 0), (int(endX), 50),
                          color.tolist(), -1)
            startX = endX

    #return cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)
        return cv2.cvtColor(bar,cv2.COLOR_RGB2BGR)

###########################################

# 쿨/웜 예측하기


def color_predict(frame):
    img = Image.open(frame) 
    
    
    fr0 = cv_imread(frame)
    fr1 = cv2.cvtColor(fr0, cv2.COLOR_BGR2RGB)
    fr = align_faces(fr1)
    fr = fr[0]    
    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)

    rects = detector(gray, 0)

    for k, d in enumerate(rects):
        shape = predictor(gray, d)
        shape = face_utils.shape_to_np(shape)
#        for (x, y) in shape:
#            cv2.circle(fr, (x, y), 2, (0, 255, 0), -1)

    point1 = ((shape[57] + shape[8]) * 0.5).round()  # point1 턱 (밑입술 하단 - 턱끝 )
    # point2 왼쪽 뺨 (왼쪽 외곽선 - 왼쪽 입술 끝점)
    point2 = ((shape[2] + shape[48]) * 0.5).round()
    # point3 오른쪽 뺨 (오른쪽 외곽선 - 오른쪽 입술 끝점)
    point3 = ((shape[14] + shape[54]) * 0.5).round()
    point4 = shape[29].astype('float64')  # point4 코
    point5 = ((shape[21] + shape[22]) * 0.5).round()  # point5 눈썹 사이

    # RGB 모드로 변경
    #rgb_img = img.convert('RGB')
    fro = Image.fromarray(fr)
    rgb_img = fro.convert('RGB')
    # 지정한 좌표의 색상을 r,g,b 변수에 넣음
    r1, g1, b1 = rgb_img.getpixel((point1[0], point1[1]))
    r2, g2, b2 = rgb_img.getpixel((point2[0], point2[1]))
    r3, g3, b3 = rgb_img.getpixel((point3[0], point3[1]))
    r4, g4, b4 = rgb_img.getpixel((point4[0], point4[1]))
    r5, g5, b5 = rgb_img.getpixel((point5[0], point5[1]))

    # RGB -> HSV
    def revised_rgb_to_hsv(r, g, b):
        (h, s, v) = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h *= 360
        s *= 100
        v *= 100
        return round(h), round(s), round(v)

    h1, s1, v1 = revised_rgb_to_hsv(r1, g1, b1)
    h2, s2, v2 = revised_rgb_to_hsv(r2, g2, b2)
    h3, s3, v3 = revised_rgb_to_hsv(r3, g3, b3)
    h4, s4, v4 = revised_rgb_to_hsv(r4, g4, b4)
    h5, s5, v5 = revised_rgb_to_hsv(r5, g5, b5)

    point1 = np.array([h1, s1, v1, r1, g1, b1])
    point2 = np.array([h2, s2, v2, r2, g2, b2])
    point3 = np.array([h3, s3, v3, r3, g3, b3])
    point4 = np.array([h4, s4, v4, r4, g4, b4])
    point5 = np.array([h5, s5, v5, r5, g5, b5])

    points = np.array([point1, point2, point3, point4, point5])
    # 정규화
    points = preprocessing.StandardScaler().fit(points).transform(points)

    # 예측하기
    predict = xgb_model.predict(points)
    predict_proba = xgb_model.predict_proba(points)

    # 쿨톤
    proba_cool = []
    for i in range(5):
        if predict_proba[i][0] > 0.5:
            proba_cool.append(predict_proba[i][0])
    # 웜톤
    proba_warm = []
    for i in range(5):
        if predict_proba[i][1] > 0.5:
            proba_warm.append(predict_proba[i][1])

    # 문구 출력
    if predict.sum() >= 3:
        result = ["웜톤일 확률이 {:.2f}% 입니다.".format(
            sum(proba_warm) / len(proba_warm) * 100)]
    else:
        result = ["쿨톤일 확률이 {:.2f}% 입니다.".format(
            sum(proba_cool) / len(proba_cool) * 100)]

    return result

