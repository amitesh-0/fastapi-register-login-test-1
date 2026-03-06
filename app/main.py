from fastapi import FastAPI
from . import models, auth
from .database import engine 
from .routers import user


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)
    
@app.get("/")
def read_root():
    return {"Hello": "World"}


