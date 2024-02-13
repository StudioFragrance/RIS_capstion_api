import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from transformers import BlipProcessor, BlipForConditionalGeneration

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from image_util import get_image_from_url


def print_caption_on_img(image: Image, caption: str, font_name: str = 'arial.ttf', size: int = 24) -> Image:
    '''
    이미지에 캡션을 추가하여 반환함
    :param image: 이미지
    :param caption: 캡션
    :param font_name: 폰트 이름
    :param size: 글자 크기
    :return: 캡션이 추가된 이미지
    '''
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_name, size=size)
    draw.text((0, 0), caption, font=font)

    return image


def get_image_caption(image: Image) -> str:
    '''
    이미지를 입력받아 이미지 캡션을 반환함
    :param image: 이미지
    :return: 이미지 캡션
    '''
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    return caption


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", required=True,
                    help="path of image")
    args = vars(ap.parse_args())
    path = args['path']

    img = get_image_from_url(path)
    text = get_image_caption(image=img)

    print(text)
    print_caption_on_img(img, text, size=50).show()
