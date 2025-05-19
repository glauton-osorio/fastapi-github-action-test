from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, models, database

app = FastAPI()

@app.post("/users/", response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(database.get_db)):
    return await crud.create_user(db, user)

@app.get("/users/", response_model=list[schemas.UserOut])
async def read_users(db: AsyncSession = Depends(database.get_db)):
    return await crud.get_users(db)
