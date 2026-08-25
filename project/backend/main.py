from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import auth, users, friends,websocket_chat
from backend.database import engine,Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )
    yield
    print("Database created")
    await engine.dispose()

app = FastAPI(title="WhatsApp Clone",lifespan=lifespan,)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(users.router)
app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(websocket_chat.router)

