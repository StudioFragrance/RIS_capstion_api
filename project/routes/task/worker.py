import os
import sys
import time

from celery import Celery, group
from celery.result import AsyncResult

sys.path.append(os.path.dirname(os.path.abspath("../../utils")))

from utils.FER import FER_image
from utils.ImageCaption import image_caption
from utils.gpt import gpt
from utils.image_util import image_util


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="create_task")
def create_task(image_path: str, user_text: str):
    # FER, image Caption 동시 실행
    task_group = group(FER_task.s(image_path), image_caption_task.s(image_path))
    result_group = task_group.apply_async()

    # GPT 결과 생성을 위해 작업 1과 2의 결과를 가져옴
    FER_result = result_group.get()[0]
    caption_result = result_group.get()[1]

    # GPT를 이용한 결과 생성
    final_result = gpt_create_task.delay(FER_result, caption_result, user_text)

    return final_result

@celery.task(name="FER_task")
def FER_task(image_path: str):
    img = image_util.get_image_from_url(image_path)
    result = FER_image.fer_json(image=img)

    return result

@celery.task(name="image_caption_task")
def image_caption_task(image_path: str):
    img = image_util.get_image_from_url(image_path)
    result = image_caption.get_image_caption(image=img)
    
    return result


@celery.task(name="gpt_create_task")
def gpt_create_task(FER_result: str, caption_result: str, user_text: str):
    
    result = gpt.make_response(FER_result, caption_result, user_text)

    return result.json()



def calculate_progress(task_list: list[str]):
    # 작업 진행 상황 계산
    total_tasks = len(task_list)  # 전체 작업 수
    completed_tasks = 0  # 완료된 작업 수

    result = []
    for task in task_list:
        task_result = AsyncResult(task)
        
        result.append({
            "task_id": task_result.id,
            "task_status": task_result.status,
            "task_result": task_result.result
        })

        if task_result.status == "SUCCESS": 
            completed_tasks += 1

    return {"progress": completed_tasks/total_tasks * 100, "result": result}
    

# 진행 상황 계산 테스크 실행
progress_task = calculate_progress.delay()

# 진행 상황 출력
print(progress_task.get())

# 작업 완료까지 대기
final_result = progress_task.get()

# 최종 결과 출력
print(final_result)



    
# @celery.task(name="create_task")
# def create_task(task_type):
#     time.sleep(10)
#     return True


@celery.task(name="gpt_task", base=GPT_Task)
def gpt_task(image_path:str, story:str):
    time.sleep(10)
    return story