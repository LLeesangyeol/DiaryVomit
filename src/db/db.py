import sqlite3
import os
from contextlib import contextmanager

# DB 파일 경로 설정 (프로젝트 루트를 기준으로 data 폴더 안에 위치)
# 현재 database.py는 src 폴더에 있으므로, 상위 폴더(..)의 data 폴더를 지정합니다.
DB_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'diary_app.db')

@contextmanager
def get_db_connection():
    """DB 연결을 관리하고, 자동 커밋/롤백을 처리하는 컨텍스트 매니저"""
    conn = None
    try:
        # DB 파일이 없으면 자동으로 생성됨
        conn = sqlite3.connect(DB_FILE_PATH)
        conn.row_factory = sqlite3.Row  # 컬럼 이름을 사용하여 데이터 접근 가능하게 설정
        yield conn
    except sqlite3.Error as e:
        print(f"SQLite 연결 오류: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def setup_database():
    """데이터베이스 파일 생성 및 모든 테이블을 초기화합니다."""
    
    print(f"데이터베이스 파일 경로: {DB_FILE_PATH}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. 사용자 테이블 (users): 회원 정보 저장
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,  -- 사용자 ID (고유해야 함)
                password_hash TEXT NOT NULL,    -- 해시된 비밀번호 (보안 필수)
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. 일기 테이블 (diaries): 사용자가 작성한 원본 일기 저장
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                diary_text TEXT NOT NULL,
                diary_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 3. 분석 결과 테이블 (analysis_results): LLM 분석 결과 저장
        # JSON 스키마의 모든 필드를 개별 컬럼으로 분리하여 검색 용이성을 높입니다.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diary_id INTEGER NOT NULL UNIQUE,  -- 일기 1개당 분석 결과 1개
                primary_emotion TEXT,              -- 기쁨, 슬픔 등
                secondary_emotions_json TEXT,      -- 보조 감정 (JSON 배열 형태로 저장)
                emotion_intensity INTEGER,         -- 0~100 점수
                analysis_score REAL,               -- -10.0 ~ +10.0 점수
                keywords_json TEXT,                -- 키워드 (JSON 배열 형태로 저장)
                summary TEXT,
                emotion_tags_json TEXT,            -- 감정 태그 (JSON 배열 형태로 저장)
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diary_id) REFERENCES diaries (id) ON DELETE CASCADE
            );
        """)
        
        conn.commit()
        print("✅ 데이터베이스와 모든 테이블(users, diaries, analysis_results)이 성공적으로 설정되었습니다.")
        
if __name__ == "__main__":
    setup_database()