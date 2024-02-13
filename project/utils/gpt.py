import os
import sys
from openai import OpenAI, Stream, ChatCompletionChunk

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from .FER.FER_image import fer_json
from ImageCaption.image_caption import get_image_caption
from image_util import get_image_from_url

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def make_prompt(caption: str, json: list, user_text: str) -> str:
    return (f"""
    [사용자 이미지를 분석한 결과]
    {caption}
    
    [사용자 텍스트]
    {user_text}
    
    [사용자 표정에서 보이는 감정]
    {str(json)}
    
    [향의 종류]
    CITRUS – 오렌지, 레몬 등 새콤달콤한 특성을 지닌 과일의 향.
    FRUITY – 농익은 과일의 달콤한 향.
    GREEN – 풀, 잎, 줄기 등을 연상시키는 신선한 향.
    AROMATIC – 로즈메리, 라벤더 등 허브 계열을 표현한 향.
    LIGHT – 프레시, 시트러스, 그린과 같이 휘발성이 높은 향으로 지속 시간이 짧다.
    HEAVY – 무겁게 가라앉아 지속력이 높은 향.
    FLORAL – 달콤한 꽃향기.
    SMOKY – 그을린 듯한 향.
    INCENSE – 인센스 스틱을 태워서 나는 듯한 향.
    ORIENTAL – 동양적인 향으로 발삼, 레진, 스파이시, 우디, 애니멀 향 등을 표현.
    SPICY – 톡 쏘는 듯한 자극적이고 강한 향.
    ANIMALIC – 동물성 향료에서 유래한 것으로 희석하여 사용할 경우 따듯한 느낌을 준다.
    LEATHER – 가죽 특유의 향.
    EARTHY – 흙, 산림 등 대지에서 비롯된 향.
    MUSK – 사향노루에서 추출한 향으로 따듯하고 포근한 느낌의 관능적인 향.
    DRY – 마른 나무, 이끼, 건초에서 느껴지는 건조한 향.
    ABSOLUTE – 식물에서 추출한 천연 향료.
    CHYPRE – 시원한 식물 향.
    WATERY – 물에서 느껴지는 상쾌하고 투명한 향.
    MARINE – 시원한 물과 해초류에서 느껴지는 짭조름한 느낌을 표현한 향.
    RESINOID – 송진, 식물 등에서 추출해 담은 향.
    BOUQUET – 다채로운 꽃이 혼합된 꽃다발에서 느껴지는 향.
    CHORD – 화음이라는 뜻으로 개별적인 향을 섞어 탄생한 새로운 형태의 향.
    BITTER – 나무뿌리, 약초, 애니멀 노트 등 서로 다른 성격의 여러 향이 복합되어 만들어낸 향.
    NUANCE – 향의 이미지를 연상시키는 향.
    HARMONY – 여러 향을 조합해 탄생한 새로운 향.
    TRAIL – 향수를 뿌린 후 지속되는 향의 여운, 잔향.
    
    위의 입력을 참고하여 향수라는 단어를 사용하지 않고, 사용자에게 어울릴 만한 적절한 향 또는 향의 조합을 추천 이유와 향의 설명과 함께 5가지 이상 리스트 형식으로 추천 해줘
    """)

def make_response(caption: str, json: list, user_text: str) -> Stream[ChatCompletionChunk]:
    return client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "너는 향기에 처음 입문하여 자신의 취향을 잘 모르는 고객에게 향을 추천해주는 조향사야",
            },
            {
                "role": "user",
                "content": make_prompt(caption, json, user_text),
            }
        ],
        model="gpt-3.5-turbo",
        stream=True,
    )


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
