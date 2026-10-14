import time
from datetime import datetime
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import  CORSMiddleware
from fastapi.params import Depends
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from slowapi import _rate_limit_exceeded_handler
from supabase import create_client

from app.routers import community, public_community, ambassador, event
from app.dependencies import get_current_user
from app.config import settings
from app.limiter import limiter


from app.database import supabase

app = FastAPI(title= "Escrow Api", version= "0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    now = datetime.now().strftime("%H:%M:%S")
    print(
        f"[{now}] {request.method} {request.url.path} "
        f"-> {response.status_code} ({duration_ms:.1f} ms)"
    )
    return response

app.include_router(community.router)
app.include_router(public_community.router)
app.include_router(ambassador.router)
app.include_router(event.router)
@app.get("/")
def home():
    return {"message": "Server is running"}

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login(request:Request, data: LoginRequest):
    client = create_client(settings.supabase_url, settings.supabase_secret_key)
    try:
        result = client.auth.sign_in_with_password(
            {
                "email" :data.email, "password": data.password
            }
        )
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong email or password")
    return {"access_token": result.session.access_token}

@app.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.get("/health")
def health_check():
    return {"status": "ok"}