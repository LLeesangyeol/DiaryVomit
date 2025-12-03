import sqlite3

DB_PATH = "app.db"

class ValidationError(Exception):
    pass

class UserAlreadyExists(Exception):
    pass

def get_connection():
    return sqlite3.connect(DB_PATH)

# -----------------------------
# DB 초기화
# -----------------------------
def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

# -----------------------------
# 회원가입
# -----------------------------
def register(id: str, password: str, username: str):

    id = (id or "").strip()
    password = (password or "").strip()
    username = (username or "").strip()

    if not id or not password or not username:
        raise ValidationError("아이디, 비밀번호, 이름은 모두 필수입니다.")

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (id, password, username) VALUES (?, ?, ?)",
                (id, password, username)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            # PRIMARY KEY 충돌(id), UNIQUE(username)
            if "users.id" in str(e):
                raise UserAlreadyExists("이미 존재하는 아이디입니다.")
            if "users.username" in str(e):
                raise UserAlreadyExists("이미 사용 중인 이름입니다.")
            raise

# -----------------------------
# 로그인
# -----------------------------
def login(id: str, password: str):

    id = (id or "").strip()
    password = (password or "").strip()

    if not id or not password:
        return False, "아이디와 비밀번호를 입력하세요.", None

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, password, username FROM users WHERE id = ?",
            (id,)
        )
        row = cur.fetchone()

    if row is None:
        return False, "존재하지 않는 아이디입니다.", None

    db_id, db_password, db_username = row

    if db_password != password:
        return False, "비밀번호가 올바르지 않습니다.", None

    # 로그인 성공
    user = {
        "id": db_id,
        "username": db_username
    }

    return True, "로그인 성공", user

# -----------------------------
# 프로필
# -----------------------------
def get_profile(user: dict):
    return { "username": user["username"] }

