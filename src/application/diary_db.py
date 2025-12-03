import sqlite3
from pathlib import Path

DB_PATH = "diary.db"

class ValidationError(Exception):
    pass

class UserAlreadyExists(Exception):
    pass

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    
    # 사용자 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 일기 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            primary_emotion TEXT,
            secondary_emotions TEXT,
            emotion_intensity INTEGER,
            analysis_score INTEGER,
            keywords TEXT,
            emotion_tags TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def register_user(username, password):
    """사용자 회원가입"""
    if not username or not password:
        raise ValidationError("아이디와 비밀번호를 입력해주세요")
    
    if len(username) < 3:
        raise ValidationError("아이디는 3자 이상이어야 합니다")
    
    if len(password) < 4:
        raise ValidationError("비밀번호는 4자 이상이어야 합니다")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 비밀번호 해싱 (간단한 방법, 실제로는 bcrypt 등 사용 권장)
        import hashlib
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                      (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise UserAlreadyExists("이미 존재하는 아이디입니다")
    finally:
        conn.close()


def login_user(username, password):
    """사용자 로그인"""
    if not username or not password:
        raise ValidationError("아이디와 비밀번호를 입력해주세요")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('SELECT username FROM users WHERE username = ? AND password = ?',
                  (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return user[0]
    else:
        raise ValidationError("아이디 또는 비밀번호가 올바르지 않습니다")

def save_diary_to_db(user_id, date_str, content, analysis=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if analysis:
        import json
        cursor.execute('''
            INSERT INTO diaries 
            (user_id, date, content, primary_emotion, secondary_emotions, emotion_intensity,
             analysis_score, keywords, emotion_tags, summary)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id,
            date_str,
            content,
            analysis.get('primary_emotion'),
            json.dumps(analysis.get('secondary_emotions', []), ensure_ascii=False),
            analysis.get('emotion_intensity'),
            analysis.get('analysis_score'),
            json.dumps(analysis.get('keywords', []), ensure_ascii=False),
            json.dumps(analysis.get('emotion_tags', []), ensure_ascii=False),
            analysis.get('summary')
        ))
    else:
        cursor.execute('''
            INSERT INTO diaries (user_id, date, content)
            VALUES (?,?,?)
        ''', (user_id, date_str, content))

    conn.commit()
    conn.close()


def get_all_diaries(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, content, primary_emotion 
        FROM diaries 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    diaries = cursor.fetchall()
    conn.close()
    return diaries


def get_diaries_for_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, date, primary_emotion, emotion_intensity 
        FROM diaries 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    all_diaries = cursor.fetchall()

    cursor.execute('''
        SELECT primary_emotion, COUNT(*), AVG(emotion_intensity)
        FROM diaries 
        WHERE user_id = ? AND primary_emotion IS NOT NULL
        GROUP BY primary_emotion
        ORDER BY COUNT(*) DESC
    ''', (user_id,))
    emo_sum = cursor.fetchall()

    conn.close()
    return all_diaries, emo_sum