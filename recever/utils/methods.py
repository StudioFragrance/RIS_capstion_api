import json

from recever.utils.ImageCaption.image_caption import get_image_caption
from recever.utils.gpt import make_response
from recever.utils.image_util import get_image_from_url


def get_image_info(img_path: str):
    image = get_image_from_url(img_path)

    return {"caption": get_image_caption(image)}


def get_gpt_response(user_text: str, caption: str):
    return make_response(caption, user_text)


def get_gpt_response_from_image(img_path: str, user_text: str):
    data = get_gpt_response(user_text, get_image_info(img_path)).replace('`', '')
    return data
