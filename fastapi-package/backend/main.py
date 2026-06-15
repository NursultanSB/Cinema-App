import os, uuid, jwt, bcrypt, datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

DATABASE_URL = "postgresql://postgres:1234@127.0.0.1:5432/cinema_books_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. Модели БД
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_path = Column(String(255))

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    genre = Column(Integer, nullable=False)  # 1 - action, 2 - comedy, 3 - drama
    ticket_price = Column(Integer, nullable=False)
    age_rating = Column(Integer, nullable=False)
    description = Column(Text)
    poster_path = Column(String(255))

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    show_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    __table_args__ = (
        CheckConstraint('quantity >= 1', name='check_quantity_positive'),
        CheckConstraint("status IN ('active', 'refunded')", name='check_status_valid'),
    )

# Pydantic схемы
class RegisterReq(BaseModel):
    username: str
    password: str
    full_name: str

class LoginReq(BaseModel):
    username: str
    password: str

class TicketReq(BaseModel):
    movie_id: int
    show_date: datetime.date
    quantity: int

app = FastAPI(title="Cinema App API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs("static/avatars", exist_ok=True)
os.makedirs("static/images/posters", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="static/images"), name="images")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

SECRET_KEY = "super-secret-cinema-key"

def get_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(401, "Unauthorized")
    try:
        payload = jwt.decode(authorization.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.username == payload["sub"]).first()
        if not user: raise Exception
        return user
    except:
        raise HTTPException(401, "Unauthorized")

# API Эндпоинты
@app.post("/api/register", status_code=201)
async def register(req: RegisterReq, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Пользователь с таким именем уже существует")
    h_pwd = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = User(username=req.username, password_hash=h_pwd, full_name=req.full_name)
    db.add(user)
    db.commit()
    return {"message": "Регистрация прошла успешно", "user_id": user.id}

@app.post("/api/login")
async def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(401, "Неверное имя пользователя или пароль")
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    token = jwt.encode({"sub": user.username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    return {"token": token}

@app.get("/api/movies")
async def get_movies(genre: Optional[int] = None, age_rating: Optional[int] = None, sort: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Movie)
    if genre is not None: q = q.filter(Movie.genre == genre)
    if age_rating is not None: q = q.filter(Movie.age_rating == age_rating)
    if sort == "price_asc": q = q.order_by(Movie.ticket_price.asc())
    elif sort == "price_desc": q = q.order_by(Movie.ticket_price.desc())
    else: q = q.order_by(Movie.id.asc())
    return q.all()

@app.post("/api/tickets", status_code=201)
async def buy_ticket(req: TicketReq, user: User = Depends(get_user), db: Session = Depends(get_db)):
    if req.show_date < datetime.date.today():
        raise HTTPException(400, "Дата сеанса не может быть в прошлом")
    if req.quantity < 1:
        raise HTTPException(400, "Количество билетов должно быть не менее 1")
    movie = db.query(Movie).filter(Movie.id == req.movie_id).first()
    if not movie:
        raise HTTPException(404, "Фильм не найден")
    total = movie.ticket_price * req.quantity
    ticket = Ticket(user_id=user.id, movie_id=movie.id, show_date=req.show_date, quantity=req.quantity, total_price=total)
    db.add(ticket)
    db.commit()
    return {"message": "Билет успешно куплен", "ticket_id": ticket.id, "total_price": total}

@app.get("/api/profile")
async def get_profile(user: User = Depends(get_user), db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.user_id == user.id).order_by(Ticket.id.desc()).all()
    tickets_list = []
    for t in tickets:
        m = db.query(Movie).filter(Movie.id == t.movie_id).first()
        tickets_list.append({
            "id": t.id, "movie_title": m.title if m else "Неизвестный фильм",
            "show_date": t.show_date, "quantity": t.quantity, "total_price": t.total_price, "status": t.status
        })
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "avatar_path": user.avatar_path, "tickets": tickets_list}

@app.post("/api/tickets/{id}/refund")
async def refund_ticket(id: int, user: User = Depends(get_user), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == id).first()
    if not ticket: raise HTTPException(404, "Билет не найден")
    if ticket.user_id != user.id: raise HTTPException(403, "Вы не можете вернуть чужой билет")
    if ticket.status == "refunded": raise HTTPException(400, "Билет уже возвращен")
    ticket.status = "refunded"
    db.commit()
    return {"message": "Возврат билета успешно оформлен", "ticket_id": ticket.id, "status": ticket.status}

@app.post("/api/profile/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_user), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(400, "Допустимы только файлы форматов JPG и PNG")
    fn = f"{uuid.uuid4()}{ext}"
    path = f"static/avatars/{fn}"
    with open(path, "wb") as f: f.write(await file.read())
    
    if user.avatar_path:
        old_path = user.avatar_path.lstrip("/")
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass
            
    user.avatar_path = f"/static/avatars/{fn}"
    db.commit()
    return {"message": "Аватар успешно обновлен", "avatar_path": user.avatar_path}

@app.get("/test")
async def test_endpoint(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        status = "Connected successfully"
    except Exception as e:
        status = f"Connection failed: {str(e)}"
    return {"status": "success", "message": "Works!", "database": status}

# Раздача фронтенда
@app.get("/")
@app.get("/{page}.html")
async def serve_html(page: str = "movies"):
    p = f"../frontend/{page}.html"
    return FileResponse(p if os.path.exists(p) else "../frontend/movies.html")

app.mount("/css", StaticFiles(directory="../frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="../frontend/js"), name="js")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)