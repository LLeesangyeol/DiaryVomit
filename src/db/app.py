from flask import Flask, request, jsonify #, g (g는 현재 사용하지 않아 제거 가능)
from flask_cors import CORS # 🆕 CORS 임포트 추가
import json
from user_manager import register_user, login_user
from ollama_analyzer import analyze_diary_with_custom_model

app = Flask(__name__)
app.secret_key = 'diaryvomit' 

# 🆕 CORS 설정 추가: Vite 개발 서버 포트(5173)에서 오는 요청을 허용합니다.
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}) 
# ... (기존 API 코드들은 그대로 유지) ...