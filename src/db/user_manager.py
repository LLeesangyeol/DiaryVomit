import bcrypt
import sqlite3
# get_db_connection 함수는 같은 src 폴더의 database.py에서 가져옵니다.
from db import get_db_connection 
from typing import Optional, Dict, Any

# 암호 해싱에 사용할 솔트 라운드 (보안 강도)
SALT_ROUNDS = 12 

def hash_password(password: str) -> str:
    """bcrypt를 사용하여 비밀번호를 안전하게 해싱합니다."""
    # 문자열을 바이트로 인코딩
    password_bytes = password.encode('utf-8')
    # 솔트 생성 및 해싱
    salt = bcrypt.gensalt(rounds=SALT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # 해시 값을 문자열로 디코딩하여 반환
    return hashed_bytes.decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """입력된 비밀번호가 저장된 해시값과 일치하는지 확인합니다."""
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        # 해시 값이 잘못된 경우 (예: 저장 시 오류 발생)
        return False

def register_user(username: str, password: str) -> bool:
    """새로운 사용자를 등록합니다."""
    if not username or not password:
        print("❌ 사용자 이름과 비밀번호는 필수 입력 항목입니다.")
        return False
        
    hashed_password = hash_password(password)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # users 테이블에 username과 해시된 비밀번호를 삽입
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            print(f"✅ 회원가입 성공: 사용자 '{username}'이 등록되었습니다.")
            return True
            
    except sqlite3.IntegrityError:
        # username 컬럼에 UNIQUE 제약조건이 있어 중복 시 발생
        print(f"❌ 회원가입 실패: 사용자 이름 '{username}'은 이미 존재합니다.")
        return False
    except Exception as e:
        print(f"❌ 회원가입 중 알 수 없는 오류 발생: {e}")
        return False

def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    사용자 로그인을 시도합니다. 성공 시 사용자 정보(딕셔너리 형태)를 반환하고, 실패 시 None을 반환합니다.
    """
    if not username or not password:
        return None
        
    user_row = None
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 사용자 이름으로 DB에서 해당 사용자의 모든 정보(특히 password_hash)를 조회
            cursor.execute(
                "SELECT id, username, password_hash, email FROM users WHERE username = ?",
                (username,)
            )
            # conn.row_factory = sqlite3.Row 덕분에 딕셔너리처럼 접근 가능한 형태로 반환됨
            user_row = cursor.fetchone() 

    except Exception as e:
        print(f"❌ 로그인 중 DB 조회 오류 발생: {e}")
        return None
        
    if user_row:
        stored_hash = user_row['password_hash']
        # 입력된 비밀번호와 저장된 해시 값을 비교
        if check_password(password, stored_hash):
            print(f"✅ 로그인 성공: 사용자 '{username}' 환영합니다.")
            
            # 비밀번호 해시를 제외한 사용자 데이터를 딕셔너리 형태로 반환
            return dict(user_row) 
        else:
            print("❌ 로그인 실패: 비밀번호가 일치하지 않습니다.")
            return None
    else:
        print(f"❌ 로그인 실패: 사용자 이름 '{username}'을 찾을 수 없습니다.")
        return None