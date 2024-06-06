from PIL.Image import Image

from recever.utils.FER.FER_image import fer_json
from recever.utils.ImageCaption.image_caption import get_image_caption
from recever.utils.gpt import make_response
from recever.utils.image_util import get_image_from_url


def get_image_info(img_path: str):
    image = get_image_from_url(img_path)
    emotion = fer_json(image)
    image_caption = get_image_caption(image)

    return {"emotion": emotion, "caption": image_caption}


def get_gpt_response(user_text: str, caption: str, emotion: list):
    return make_response(caption, emotion, user_text)


def get_gpt_response_from_image(img_path: str, user_text: str):
    image_info = get_image_info(img_path)
    return get_gpt_response(user_text, image_info["caption"], image_info["emotion"])

