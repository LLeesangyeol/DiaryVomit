import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "mood_tracker.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS diaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, content TEXT NOT NULL,
        primary_emotion TEXT, secondary_emotions TEXT, emotion_intensity INTEGER,
        analysis_score INTEGER, keywords TEXT, emotion_tags TEXT, summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_diary_to_db(date_str, content, analysis=None):
    """일기를 데이터베이스에 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if analysis:
        import json
        cursor.execute('''INSERT INTO diaries (date,content,primary_emotion,secondary_emotions,emotion_intensity,analysis_score,keywords,emotion_tags,summary) 
            VALUES (?,?,?,?,?,?,?,?,?)''', (date_str, content, analysis.get('primary_emotion'),
            json.dumps(analysis.get('secondary_emotions',[]), ensure_ascii=False),
            analysis.get('emotion_intensity'), analysis.get('analysis_score'),
            json.dumps(analysis.get('keywords',[]), ensure_ascii=False),
            json.dumps(analysis.get('emotion_tags',[]), ensure_ascii=False),
            analysis.get('summary')))
    else:
        cursor.execute('INSERT INTO diaries (date,content) VALUES (?,?)', (date_str, content))
    
    conn.commit()
    conn.close()

def get_all_diaries():
    """모든 일기 조회 (날짜, 내용, 주감정)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT date,content,primary_emotion FROM diaries ORDER BY created_at DESC')
    diaries = cursor.fetchall()
    conn.close()
    return diaries

def get_diaries_for_stats():
    """통계를 위한 일기 데이터 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id,date,primary_emotion,emotion_intensity FROM diaries ORDER BY created_at DESC')
    all_diaries = cursor.fetchall()
    cursor.execute('SELECT primary_emotion,COUNT(*),AVG(emotion_intensity) FROM diaries WHERE primary_emotion IS NOT NULL GROUP BY primary_emotion ORDER BY COUNT(*) DESC')
    emo_sum = cursor.fetchall()
    conn.close()
    return all_diaries, emo_sum