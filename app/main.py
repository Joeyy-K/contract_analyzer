from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth
from app.api.v1 import contracts
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contract Analyzer API",
    description="API for analyzing legal contracts",
    version="1.0.0",
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

app.include_router(
    contracts.router,
    prefix="/api/v1/contracts",
    tags=["contracts"]
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Contract Analyzer API"}