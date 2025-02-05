import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes import routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    pass
    yield
    pass


app = FastAPI(lifespan=lifespan)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in routers:
    app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("sender_main:app", host="0.0.0.0", port=8000, reload=True)
