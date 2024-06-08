import os
import sys

from openai import OpenAI

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from recever.utils.image_util import get_image_from_url
from recever.utils.FER.FER_image import fer_json
from recever.utils.ImageCaption.image_caption import get_image_caption

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def make_prompt(caption: str, user_text: str) -> str:
    return (f"""
    [이미지 분석]
    {caption}
    
    [고객의 취향]
    {user_text}
    
    [향기의 Note 종류]
    시트러스, 스파이시, 그린, 허브, 발사믹, 파우더리, 애니멀, 우디, 프루티, 알데하이드, 플로럴, 마린
    사용자가 좋아하는 느낌을 기반으로 각 향기 Note의 선호도를 0 (싫어함) , 1 (중립), 2(좋아함) 중의 숫자로 정리하고, 그 이유를 다음과 같은 JSON 양식으로 알려줘
    
    - 양식 : 
    """ + """
    ```
    {
       "고객의 특성" :
       "추천 어코드" :
       "선호도" : {
          "향기의 Note 종류" : {
             "Level" : 
             "Reason" : 
          }
       }
    }
    ```
    """)


def make_response(caption: str, user_text: str):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "너는 향기에 처음 입문하여 자신의 취향을 잘 모르는 고객에게 향을 추천해주는 조향사야",
            },
            {
                "role": "user",
                "content": make_prompt(caption, user_text),
            }
        ],
        model="gpt-3.5-turbo",
    )
    return str(response.choices[0].message.content)


if __name__ == "__main__":
    '''
    병렬 처리 시도 결과 프로세스 생성 등에 따른 오버헤드가 발생하여 오히려 더 느려짐
    따라서 순차 실행으로 변경
    순차실행 결과 10초대, 병렬실행 결과 60-100초대
    '''
    path = input("이미지 경로 또는 Url을 입력해주세요: ")
    img = get_image_from_url(path)

    json = fer_json(img)
    caption = get_image_caption(img)

    user_text = input("자신의 이야기를 전해주세요 : ")

    stream = make_response(caption, json, user_text)

    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")
