from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Union
import threading
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from werkzeug.security import check_password_hash

from models.database import (
    init_db, get_user_messages, save_message, get_user_by_username,
    create_user, add_task, get_user_tasks, update_task_status,
    delete_task, get_task_stats
)
from models.lstm_model import LSTMModelManager

# ─── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "yourdiary-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="YourDiary API",
    description="AI-Powered Personal Diary — REST API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth Setup ───────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
model_manager = LSTMModelManager()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class DiaryEntryRequest(BaseModel):
    message: str

class SuggestionRequest(BaseModel):
    text: str
    max_length: Union[str, int] = 20
    num_suggestions: int = 3

class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[str] = None

class TaskStatusRequest(BaseModel):
    status: str


# ─── JWT Helpers ──────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency that validates JWT and returns current user info."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return {"user_id": user_id, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("🌟 Starting YourDiary FastAPI")
    init_db()
    model_manager.load_base_model()
    print("📝 YourDiary API ready at http://localhost:8000")
    print("📖 API docs at http://localhost:8000/docs")


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "YourDiary API v2.0 🌟",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/api/health")
def health():
    return {"status": "healthy"}


# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.post("/api/auth/signup", status_code=201)
def signup(data: SignupRequest):
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long")
    if not create_user(data.username, data.password):
        raise HTTPException(status_code=409, detail="Username already exists. Please choose a different one.")
    return {"message": f"Welcome to YourDiary, {data.username}! Your personal AI assistant is ready."}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = get_user_by_username(data.username)
    if not user or not check_password_hash(user[2], data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"user_id": user[0], "username": data.username})
    return {"access_token": token, "token_type": "bearer", "username": data.username}


# ─── Diary Routes ─────────────────────────────────────────────────────────────
@app.post("/api/diary/entry")
def save_entry(data: DiaryEntryRequest, current_user: dict = Depends(get_current_user)):
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Diary entry cannot be empty")

    save_message(current_user["user_id"], message)

    recent_messages = get_user_messages(current_user["user_id"], limit=10)
    message_texts = [msg[0] for msg in recent_messages]
    total = len(get_user_messages(current_user["user_id"]))

    # Background AI training every 3 entries
    if total % 3 == 0 and total > 0:
        print(f"🎯 YourDiary: Training AI for user {current_user['user_id']} after {total} entries")
        thread = threading.Thread(
            target=model_manager.train_user_model_background,
            args=(current_user["user_id"], message_texts)
        )
        thread.daemon = True
        thread.start()

    return {"success": True, "total_entries": total}


@app.get("/api/diary/entries")
def get_entries(current_user: dict = Depends(get_current_user)):
    messages = get_user_messages(current_user["user_id"])
    return {
        "entries": [{"message": m[0], "timestamp": m[1]} for m in messages]
    }


@app.post("/api/diary/suggestions")
def get_suggestions(data: SuggestionRequest, current_user: dict = Depends(get_current_user)):
    if len(data.text) < 2:
        return {"suggestions": []}

    try:
        print(f"🧠 YourDiary AI: Generating suggestions for user {current_user['user_id']}")
        user_model = model_manager.get_user_model(current_user["user_id"])

        if data.max_length == "sentence":
            suggestions = user_model.get_completions_till_period(
                data.text, num_suggestions=data.num_suggestions
            )
        else:
            max_len = int(data.max_length) if isinstance(data.max_length, (str, int)) else 20
            suggestions = user_model.get_completions(
                data.text, num_suggestions=data.num_suggestions, max_length=max_len
            )

        print(f"✅ Generated {len(suggestions)} suggestions")
        return {"suggestions": suggestions}

    except Exception as e:
        print(f"❌ AI Error: {e}")
        fallback = [
            " feels meaningful to me",
            " brings me joy",
            " is something I want to remember",
        ]
        return {"suggestions": fallback[: data.num_suggestions]}


# ─── Task Routes ──────────────────────────────────────────────────────────────
@app.get("/api/tasks")
def get_tasks(current_user: dict = Depends(get_current_user)):
    tasks = get_user_tasks(current_user["user_id"])
    stats = get_task_stats(current_user["user_id"])
    return {"tasks": tasks, "stats": stats}


@app.post("/api/tasks", status_code=201)
def create_task(data: TaskCreateRequest, current_user: dict = Depends(get_current_user)):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")
    due = data.due_date if data.due_date else None
    if add_task(current_user["user_id"], data.title, data.description, data.priority, due):
        return {"success": True}
    raise HTTPException(status_code=500, detail="Failed to create task")


@app.patch("/api/tasks/{task_id}/status")
def update_task(task_id: int, data: TaskStatusRequest, current_user: dict = Depends(get_current_user)):
    if update_task_status(task_id, data.status, current_user["user_id"]):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: int, current_user: dict = Depends(get_current_user)):
    if delete_task(task_id, current_user["user_id"]):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Task not found")


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
