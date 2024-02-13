import os

import PIL
import requests
import validators
from PIL import Image


def get_image_from_url(url: str) -> Image:
    '''
    url이 주어지면 해당 url의 이미지를 가져오거나, 파일 경로가 주어지면 해당 파일의 이미지를 가져옴
    :param url: 이미지의 url 또는 파일 경로
    :return: 이미지
    '''
    try:
        if validators.url(url):
            return Image.open(requests.get(url, stream=True).raw).convert('RGB')
        else:
            if os.path.isfile(url):
                return Image.open(url).convert('RGB')
            else:
                raise FileNotFoundError(f"File {url} not found")

    except PIL.UnidentifiedImageError:
        raise FileNotFoundError(f"{url} is not an image")
