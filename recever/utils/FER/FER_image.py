import argparse
import os

import cv2
import numpy as np
import torchvision.transforms as transforms
from PIL import Image

from recever.utils.FER.model import *
from recever.utils.image_util import get_image_from_url


def get_abs_path(target: str) -> str:
    '''
    현재 스크립트의 디렉토리를 기준으로 상대 경로를 절대 경로로 변환함
    :param target: 상대 경로
    :return: 절대 경로
    '''
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), target)


def load_trained_model(model_path: str) -> Face_Emotion_CNN:
    model = Face_Emotion_CNN()
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage), strict=False)

    return model


def draw_box_image(
        image: Image,
        box: tuple[int, int, int, int],
        msg: str = "",
        color: tuple[int, int, int] = (0, 0, 255),
        thick: int = 2) -> Image:
    '''
    이미지에 박스를 그리고, 박스에 메시지를 추가하여 반환함
    :param image: 이미지
    :param box: 박스 좌표
    :param msg: 박스에 추가할 메시지
    :param color: 박스 색깔
    :param thick: 박스 두께
    :return: 박스가 그려진 이미지
    '''
    image = pil2opencv(image)
    (x1, y1, x2, y2) = box

    y = y1 - 10 if y1 - 10 > 10 else y1 + 10
    text = f"{msg} ( {str(x1)}, {str(y1)} )"
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thick)
    cv2.putText(image, text, (x1, y), cv2.LINE_AA, 0.45, color, thick)

    return opencv2pil(image)


def draw_box_image_list(
        image: Image,
        box: list[tuple[int, int, int, int]],
        msg: str = "",
        color: tuple[int, int, int] = (0, 0, 255),
        thick: int = 2) -> Image:
    '''
    박스 좌표 리스트를 받아 이미지에 박스를 그리고, 박스에 메시지를 추가하여 반환함
    :param image: 이미지
    :param box: 박스 좌표 리스트
    :param msg: 박스에 추가할 메시지
    :param color: 박스 색깔
    :param thick: 박스 두께
    :return: 박스가 그려진 이미지
    '''

    for box, index in zip(box, range(len(box))):
        image = draw_box_image(image, box, f"{msg} {index}", color, thick)

    return image


def pil2opencv(image: Image) -> np.ndarray:
    '''
    PIL 이미지를 opencv 이미지로 변환
    :param image: PIL 이미지
    :return: opencv 이미지
    '''
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def opencv2pil(image: np.ndarray) -> Image:
    '''
    opencv 이미지를 PIL 이미지로 변환
    :param image: opencv 이미지
    :return: PIL 이미지
    '''
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def face_detection(image: Image, confidence_minimum: float = 0.5) -> list[tuple[int, int, int, int]]:
    '''
    이미지에서 얼굴을 찾아서 얼굴의 좌표를 반환함
    :param image: 이미지
    :param confidence_minimum: 얼굴로 판단할 최소 확률
    :return: 얼굴 좌표 리스트
    '''
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct paths relative to the current script's directory
    prototxt_path = get_abs_path("./models/weights-prototxt.txt")
    caffe_model_path = get_abs_path("models/res_ssd_300Dim.caffeModel")

    # load SSD and ResNet network based caffe model for 300x300 dim imgs
    net = cv2.dnn.readNetFromCaffe(prototxt_path, caffe_model_path)
    image = pil2opencv(image)

    (height, width) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                                 (300, 300), (104.0, 177.0, 123.0))

    # pass the blob into the network
    net.setInput(blob)
    detections = net.forward()

    faces = []
    for i in range(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with the
        # prediction
        confidence = detections[0, 0, i, 2]

        # greater than the minimum confidence
        if confidence > confidence_minimum:
            box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
            (x1, y1, x2, y2) = box.astype("int")
            faces.append((x1, y1, x2, y2))

    return faces


def facial_expression_recognition(image: Image, face_pos_list: list[tuple[int, int, int, int]]) -> list[dict]:
    '''
    이미지에서 얼굴의 좌표를 받아서 감정을 인식하고, 감정과 감정 확률을 반환함
    :param image: 이미지
    :param face_pos_list: 얼굴 좌표 리스트
    :return: 감정과 감정 확률 리스트(JSON 형태)
    '''
    model = load_trained_model(get_abs_path('./models/FER_trained_model.pt'))

    emotion_dict = {0: 'neutral', 1: 'happiness', 2: 'surprise', 3: 'sadness',
                    4: 'anger', 5: 'disguest', 6: 'fear'}

    val_transform = transforms.Compose([
        transforms.ToTensor()])

    image = pil2opencv(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    json = []

    for (x1, y1, x2, y2) in face_pos_list:
        resize_frame = cv2.resize(gray[y1:y2, x1:x2], (48, 48))
        X = resize_frame / 256
        X = Image.fromarray((resize_frame))
        X = val_transform(X).unsqueeze(0)
        with torch.no_grad():
            model.eval()
            log_ps = model.cpu()(X)
            ps = torch.exp(log_ps)
            top_p, top_class = ps.topk(1, dim=1)
            pred = emotion_dict[int(top_class.numpy().item())]

            emotion_probs = {emotion: float(prob) * 100 for emotion, prob in
                             zip(emotion_dict.values(), ps.numpy().flatten())}

        json.append({
            "emotion": pred,
            "emotion_probs": emotion_probs,
            "box": {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            }
        })

    return json


def fer_json(image: Image) -> list:
    '''
    이미지를 입력받아 감정을 인식하고, 감정과 감정 확률을 반환함
    :param image: 이미지
    :return: 감정과 감정 확률 리스트(JSON 형태)
    '''
    face_list = face_detection(image)
    json = facial_expression_recognition(image, face_list)

    return json


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", required=True, help="path of image")
    args = vars(ap.parse_args())
    path = args['path']

    image = get_image_from_url(path)
    face_list = face_detection(image)
    json = facial_expression_recognition(image, face_list)

    # show the output image
    print(json)
    draw_box_image_list(image, face_list, "face").show()
