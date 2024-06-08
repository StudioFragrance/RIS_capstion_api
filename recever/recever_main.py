import os
import sys

from starlette.config import Config

from core.pipline.rpc.message_broker import MessageBroker

config = Config('.env')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recever.utils import methods

broker = MessageBroker("localhost:9092")
# methods 모듈은 내부에 echo 함수를 가지고 있음
broker.serve(methods, config('TOPIC_NAME'))
