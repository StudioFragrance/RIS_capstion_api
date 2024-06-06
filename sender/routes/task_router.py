import os
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from starlette.config import Config

from sender.core.pipline.rpc.message_broker import MessageBroker
from sender.utils import image_util
from sender.utils.image_util import get_image_from_url

host = "localhost"
port = 9092

broker = MessageBroker(f"{host}:{port}")

config = Config('../.env')

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=201)
def run_all_task(file: UploadFile, story: str) -> JSONResponse:
    '''
    Run a new task.
    :param file: UploadFile
    :param story: str
    :return: JSONResponse
    
    description:
        다음과 같은 이유로 해당 함수는 object를 받아들이지 않는다.
        fastapi 에 있는 공식 문서 중 경고 부분을 참고.
        
        You can declare multiple File and Form parameters in a path operation, 
        but you can't also declare Body fields that you expect to receive as JSON, 
        as the request will have the body encoded using multipart/form-data instead of application/json.
        
        This is not a limitation of FastAPI, it's part of the HTTP protocol.
        
        fastapi docs: (https://fastapi.tiangolo.com/tutorial/request-files/)
        MDN 웹 문서POST: (https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST)
        HTTP/3: RFC 8441 (https://tools.ietf.org/html/rfc8441)
        RFC 7578: "Returning Values from Forms: multipart/form-data" (https://tools.ietf.org/html/rfc7578)

        [필요시 대안]
        1. 파일을 FormData로 전송: 파일을 multipart/form-data 형식으로 전송하고, 객체는 쿼리 매개변수나 경로 매개변수로 전달할 수 있습니다. 이렇게 하면 파일과 객체를 동시에 전송할 수 있습니다.
            async def upload_file(file: UploadFile = File(...), object_data: str = Form(...)):
                # 파일 및 객체 처리 로직
        2. 파일을 객체에 포함하여 전송: 파일을 객체에 포함하여 JSON 형식으로 전송할 수 있습니다. 예를 들어, 파일 데이터를 Base64 문자열로 인코딩하여 JSON 객체에 포함시킬 수 있습니다.
            async def upload_file(data: str):
                # Base64 디코딩 및 파일 처리 로직
    '''
    Path("./file/").mkdir(parents=True, exist_ok=True)

    # save the file 
    with open(f".file/{file.filename}", "wb") as buffer:
        buffer.write(file.file.read())

    image_info = os.path.abspath(f"./file/{file.filename}")

    return broker.rpc(config('TOPIC_NAME'), "get_gpt_response_from_image", image_info, story)


@router.post("/img", status_code=201)
def get_image_info(file: UploadFile):
    '''
    Get image info.
    :param file: UploadFile
    :return: JSONResponse

    description:
        이미지를 제공하면 사진 내 사람에 대한 감정 분석 및 사진의 캡션을 생성합니다.
    '''


    Path("./file/").mkdir(parents=True, exist_ok=True)

    # save the file
    with open(f"./file/{file.filename}", "wb") as buffer:
        buffer.write(file.file.read())

    # get image info
    image_info = os.path.abspath(f"./file/{file.filename}")

    return broker.rpc(config('TOPIC_NAME'), "get_image_info", image_info)


@router.get("/gpt")
def get_gpt_response(story: str, img_caption: str, img_emotion: str) -> JSONResponse:
    '''
    Get GPT response.
    :param story:
    :param img_caption:
    :param img_emotion:
    :return:

    description:
        이미지 캡션, 감정 및 사용자 텍스트를 사용하여 GPT-API를 사용하여 응답을 생성합니다.
    '''

    return broker.rpc(config('TOPIC_NAME'), "get_gpt_response", story, img_caption, img_emotion)
