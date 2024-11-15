from datetime import timedelta
from functools import cache
import logging
from fastapi import Depends, FastAPI
from minio import Minio
from typing import Annotated, List
from sqlmodel import SQLModel
from pydantic import SerializationInfo, field_serializer
import uuid
from cachetools.func import ttl_cache

app = FastAPI()

def get_minio_client():
    return Minio(
        "localhost:9000",
        access_key="PgTMaOi21QzMk8mWERru",
        secret_key="73jYFGrUPWYkmeNJoy2TXMob1wEFyGyahTkwOMAo",
        secure=False
    )


MinioDep = Annotated[Minio, Depends(get_minio_client)]


class MyModel(SQLModel):
  id: uuid.UUID
  resource: str


context = None

def get_context():
  logging.warning("Called get_context")
  return dict(
    minio = get_minio_client(),
    bucket = "hola"
  )

class MyModelPublic(MyModel):
  resource: str

  @field_serializer('resource')
  def presign_url(self, v: str, _info: SerializationInfo):
    if not v:
        return v
    return self.get_presigned_url(v)

  @classmethod
  def get_presigned_url(cls, v: str):
    global context
    if context is None:
      context = get_context()
    minio = context["minio"]
    mybucket = context["bucket"]
    return minio.get_presigned_url(
        "GET",
        mybucket,
        v,
        expires=timedelta(days=1)
    )


class MyModelsPublic(SQLModel):
  data: List[MyModelPublic]
  count: int

@app.get("/{id}", response_model=MyModelPublic)
def read_detail(id: str):
    mymodel = MyModel(id=uuid.uuid4(), resource="file.mp3")
    return mymodel

@app.get("/", response_model=MyModelsPublic)
def read_root():
    data = [
      MyModel(id=uuid.uuid4(), resource="file.mp3"),
      MyModel(id=uuid.uuid4(), resource="file2.mp3"),
      MyModel(id=uuid.uuid4(), resource="file3.mp3"),
    ]
    
    return MyModelsPublic(data=data, count=len(data))

