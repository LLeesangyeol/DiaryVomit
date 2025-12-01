#!/usr/bin/env python3
# coding: utf-8

"""
MOOD TRACKER v1.0 - AI EMOTION ANALYSIS
감정 분석 기반 기록 추적 일기 (with AI)
EMOTION TRACKING DIARY - AI POWERED ANALYSIS
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import sqlite3
import json
import threading
import sys
import os
from pathlib import Path

# 상위 디렉토리(src)를 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ollama_analyzer import analyze_diary_with_custom_model
    HAS_ANALYZER = True
except:
    HAS_ANALYZER = False

# ========================================
# DATABASE SETUP
# ========================================
DB_PATH = Path(__file__).parent.parent.parent / "data" / "mood_tracker.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

# ========================================
# MAIN APPLICATION
# ========================================
class MoodTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("감정 분석 일기장")
        
        # DPI 인식 설정 (Windows 고해상도 지원)
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 화면 크기 설정 - 가독성을 위해 더 크게
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1500
        window_height = 950
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 850)
        
        # 색상 테마 (연하늘색 스타일)
        self.colors = {
            'bg': '#EBF5FB',           # 연한 하늘색 배경
            'panel_bg': '#D6EAF8',     # 패널 배경
            'border': '#5DADE2',       # 하늘색 테두리
            'text': '#1B4F72',         # 진한 남색 텍스트
            'text_dim': '#5499C7',     # 중간 파란색
            'input_bg': '#FFFFFF',     # 흰색 입력 배경
            'button_bg': '#5DADE2',    # 하늘색 버튼
            'button_fg': '#FFFFFF',    # 흰색 버튼 텍스트
            'accent': '#3498DB',       # 액센트 파란색
            'hover': '#AED6F1'         # 호버 색상
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 데이터베이스 초기화
        init_database()
        
        # 현재 분석 결과
        self.current_analysis = None
        
        # 메뉴 또는 메인 UI 표시 여부
        self.main_content = None
        
        # UI 구성 - 먼저 메뉴 표시
        self.show_menu()
        
    def show_menu(self):
        """메뉴 화면 표시"""
        # 기존 컨텐츠 제거
        if self.main_content:
            self.main_content.destroy()
        
        # 메뉴 프레임
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        # 중앙 컨테이너
        center_frame = tk.Frame(self.main_content, bg=self.colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 타이틀
        title_label = tk.Label(center_frame,
                              text="감정 분석 일기장",
                              font=("굴림", 36, "bold"),
                              bg=self.colors['bg'],
                              fg=self.colors['accent'])
        title_label.pack(pady=(0, 15))
        
        subtitle_label = tk.Label(center_frame,
                                 text="감정을 분석해주는 일기장",
                                 font=("굴림", 18),
                                 bg=self.colors['bg'],
                                 fg=self.colors['text_dim'])
        subtitle_label.pack(pady=(0, 50))
        
        # 메뉴 버튼들
        button_frame = tk.Frame(center_frame, bg=self.colors['bg'])
        button_frame.pack()
        
        # 일기 작성 버튼
        write_btn = tk.Button(button_frame,
                             text="일기 작성",
                             font=("굴림", 18, "bold"),
                             bg=self.colors['accent'],
                             fg='white',
                             activebackground='#2980B9',
                             activeforeground='white',
                             relief=tk.RAISED,
                             bd=0,
                             width=18,
                             pady=18,
                             cursor="hand2",
                             command=lambda: self.create_ui('write'))
        write_btn.pack(pady=10)
        
        # 감정 통계 버튼
        analysis_btn = tk.Button(button_frame,
                                text="감정 통계",
                                font=("굴림", 18, "bold"),
                                bg=self.colors['button_bg'],
                                fg='white',
                                activebackground=self.colors['accent'],
                                activeforeground='white',
                                relief=tk.RAISED,
                                bd=0,
                                width=18,
                                pady=18,
                                cursor="hand2",
                                command=lambda: self.create_ui('analysis'))
        analysis_btn.pack(pady=10)
        
        # 기록 보기 버튼
        history_btn = tk.Button(button_frame,
                               text="내가 쓴 일기",
                               font=("굴림", 18, "bold"),
                               bg=self.colors['button_bg'],
                               fg='white',
                               activebackground=self.colors['accent'],
                               activeforeground='white',
                               relief=tk.RAISED,
                               bd=0,
                               width=18,
                               pady=18,
                               cursor="hand2",
                               command=lambda: self.create_ui('history'))
        history_btn.pack(pady=10)
        
        info_label = tk.Label(center_frame,
                            text="원하는 메뉴를 선택해주세요",
                            font=("굴림", 15),
                            bg=self.colors['bg'],
                            fg=self.colors['text_dim'])
        info_label.pack(pady=(40, 0))
    
    def create_ui(self, initial_tab='write'):
        """메인 UI 생성"""
        # 기존 메뉴 제거
        if self.main_content:
            self.main_content.destroy()
        
        # 메인 컨텐츠 프레임
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        # 상단 헤더
        self.create_header()
        
        # 선택한 탭만 생성
        if initial_tab == 'write':
            self.create_write_tab_only()
        elif initial_tab == 'analysis':
            self.create_analysis_tab_only()
        elif initial_tab == 'history':
            self.create_history_tab_only()
        
        # 하단 상태바
        self.create_statusbar()
        
    def create_header(self):
        """헤더 생성"""
        header_frame = tk.Frame(self.main_content, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        header = tk.Frame(header_frame, bg=self.colors['accent'], bd=0)
        header.pack(fill=tk.X)
        
        # 헤더 내용
        content = tk.Frame(header, bg=self.colors['accent'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title1 = tk.Label(content,
                         text="감정 분석 일기장",
                         font=("굴림", 22, "bold"),
                         bg=self.colors['accent'],
                         fg='white')
        title1.pack(pady=(18, 4))
        
        title2 = tk.Label(content,
                         text="감성을 분석해주는 일기장",
                         font=("굴림", 12),
                         bg=self.colors['accent'],
                         fg='white')
        title2.pack(pady=(4, 18))
        
        # 메뉴로 돌아가기 버튼
        back_btn = tk.Button(header,
                            text="메인 메뉴로 돌아가기",
                            font=("굴림", 15, "bold"),
                            bg=self.colors['accent'],
                            fg='white',
                            activebackground='#2980B9',
                            activeforeground='white',
                            relief=tk.FLAT,
                            bd=0,
                            padx=25,
                            pady=12,
                            cursor="hand2",
                            command=self.show_menu)
        back_btn.pack(side=tk.RIGHT, padx=20)
        
    def create_write_tab_only(self):
        """일기 작성 탭만 생성"""
        tab_container = tk.Frame(self.main_content, bg=self.colors['bg'])
        tab_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        self.create_write_content(tab_container)
    
    def create_analysis_tab_only(self):
        """감정 통계 탭만 생성"""
        tab_container = tk.Frame(self.main_content, bg=self.colors['bg'])
        tab_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        self.create_analysis_content(tab_container)
    
    def create_history_tab_only(self):
        """기록 보기 탭만 생성"""
        tab_container = tk.Frame(self.main_content, bg=self.colors['bg'])
        tab_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        self.create_history_content(tab_container)
        
    def create_write_content(self, parent):
        """일기 작성 컨텐츠"""
        self.write_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.write_frame.pack(fill=tk.BOTH, expand=True)
        
        # 메인 컨텐츠 영역
        content_area = tk.Frame(self.write_frame, bg=self.colors['bg'])
        content_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 상단: 입력 영역
        input_section = tk.Frame(content_area, bg=self.colors['bg'])
        input_section.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # 제목
        title_label = tk.Label(input_section,
                              text="오늘 하루는 어떠셨나요?",
                              font=("굴림", 15, "bold"),
                              bg=self.colors['bg'],
                              fg=self.colors['text'])
        title_label.pack(pady=(0, 12), anchor=tk.W)
        
        # 입력 영역 - 깔끔한 흰색 박스
        input_frame = tk.Frame(input_section, bg='white', relief=tk.SOLID, bd=1)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # 텍스트 입력
        self.diary_text = scrolledtext.ScrolledText(input_frame,
                                                    wrap=tk.WORD,
                                                    font=("굴림", 13),
                                                    bg='white',
                                                    fg='#2C3E50',
                                                    insertbackground=self.colors['accent'],
                                                    selectbackground=self.colors['hover'],
                                                    selectforeground=self.colors['text'],
                                                    relief=tk.FLAT,
                                                    padx=18,
                                                    pady=18)
        self.diary_text.pack(fill=tk.BOTH, expand=True)
        self.diary_text.insert(1.0, "자유롭게 작성해주세요")
        self.diary_text.bind("<FocusIn>", self.clear_placeholder)
        
        # 하단: 결과 영역
        result_section = tk.Frame(content_area, bg=self.colors['bg'])
        result_section.pack(fill=tk.BOTH, expand=True)
        
        # 결과 제목
        self.result_title_label = tk.Label(result_section,
                               text="감정 분석 결과",
                               font=("굴림", 15, "bold"),
                               bg=self.colors['bg'],
                               fg=self.colors['text'])
        self.result_title_label.pack(pady=(0, 12), anchor=tk.W)
        
        # 결과 영역 - 깔끔한 흰색 박스
        result_frame = tk.Frame(result_section, bg='white', relief=tk.SOLID, bd=1)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame,
                                                     wrap=tk.WORD,
                                                     font=("굴림", 12),
                                                     bg='white',
                                                     fg='#34495E',
                                                     relief=tk.FLAT,
                                                     padx=18,
                                                     pady=18,
                                                     state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 버튼 프레임
        button_frame = tk.Frame(self.write_frame, bg=self.colors['bg'])
        button_frame.pack(pady=15)
        
        # 감정 분석 버튼
        self.analyze_btn = tk.Button(button_frame,
                                     text="감정 분석",
                                     font=("굴림", 13, "bold"),
                                     bg=self.colors['button_bg'],
                                     fg='white',
                                     activebackground=self.colors['accent'],
                                     activeforeground='white',
                                     relief=tk.RAISED,
                                     bd=0,
                                     width=15,
                                     pady=14,
                                     cursor="hand2",
                                     command=self.analyze_emotion)
        self.analyze_btn.pack(side=tk.LEFT, padx=10)
        
        # 작성 완료 버튼
        self.save_btn = tk.Button(button_frame,
                                 text="✓ 작성 완료",
                                 font=("굴림", 13, "bold"),
                                 bg=self.colors['accent'],
                                 fg='white',
                                 activebackground='#2980B9',
                                 activeforeground='white',
                                 relief=tk.RAISED,
                                 bd=0,
                                 width=15,
                                 pady=14,
                                 cursor="hand2",
                                 command=self.save_diary)
        self.save_btn.pack(side=tk.LEFT, padx=10)
        
        # 초기화 버튼
        self.clear_btn = tk.Button(button_frame,
                                   text="새로 쓰기",
                                   font=("굴림", 13, "bold"),
                                   bg=self.colors['panel_bg'],
                                   fg=self.colors['text'],
                                   activebackground=self.colors['hover'],
                                   activeforeground=self.colors['text'],
                                   relief=tk.RAISED,
                                   bd=0,
                                   width=15,
                                   pady=14,
                                   cursor="hand2",
                                   command=self.clear_inputs)
        self.clear_btn.pack(side=tk.LEFT, padx=10)
        
    def create_analysis_content(self, parent):
        """감정 통계 컨텐츠"""
        self.analysis_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        # 안내 박스
        info_box = tk.Frame(self.analysis_frame, bg='white', relief=tk.SOLID, bd=1)
        info_box.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=450, height=300)
        
        icon_label = tk.Label(info_box,
                            font=("굴림", 48),
                            bg='white',
                            fg=self.colors['accent'])
        icon_label.pack(pady=(30, 15))
        
        title_label = tk.Label(info_box,
                              text="감정 통계 기능 준비 중",
                              font=("굴림", 18, "bold"),
                              bg='white',
                              fg=self.colors['text'])
        title_label.pack(pady=(0, 12))
        
        info_label = tk.Label(info_box,
                            text="감정 분석 통계 및 차트 기능이\n곧 제공될 예정입니다.",
                            font=("굴림", 12),
                            bg='white',
                            fg=self.colors['text_dim'],
                            justify=tk.CENTER)
        info_label.pack(pady=(0, 30))
        
    def create_history_content(self, parent):
        """기록 보기 컨텐츠"""
        self.history_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.history_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(self.history_frame,
                              text="내가 쓴 일기",
                              font=("굴림", 15, "bold"),
                              bg=self.colors['bg'],
                              fg=self.colors['text'])
        title_label.pack(pady=(18, 22), anchor=tk.W, padx=30)
        
        # 스크롤 가능한 리스트 영역
        list_frame = tk.Frame(self.history_frame, bg='white', relief=tk.SOLID, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 18))
        
        # 스크롤바와 캔버스
        self.history_canvas = tk.Canvas(list_frame,
                                       bg='white',
                                       highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame,
                                 orient="vertical",
                                 command=self.history_canvas.yview)
        
        self.history_scrollable = tk.Frame(self.history_canvas,
                                          bg='white')
        
        self.history_scrollable.bind("<Configure>",
                                    lambda e: self.history_canvas.configure(
                                        scrollregion=self.history_canvas.bbox("all")))
        
        self.history_canvas.create_window((0, 0),
                                         window=self.history_scrollable,
                                         anchor="nw")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 새로고침 버튼
        refresh_btn = tk.Button(self.history_frame,
                               text="목록 새로고침",
                               font=("굴림", 13, "bold"),
                               bg=self.colors['button_bg'],
                               fg='white',
                               activebackground=self.colors['accent'],
                               activeforeground='white',
                               relief=tk.RAISED,
                               bd=0,
                               width=22,
                               pady=14,
                               cursor="hand2",
                               command=self.load_history)
        refresh_btn.pack(pady=18)
        
    def create_statusbar(self):
        """상태바 생성"""
        status_frame = tk.Frame(self.main_content, bg=self.colors['panel_bg'], height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_frame,
                                     text="준비 완료",
                                     font=("굴림", 11),
                                     bg=self.colors['panel_bg'],
                                     fg=self.colors['text_dim'],
                                     anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=25, pady=10)
        
        time_label = tk.Label(status_frame,
                            text=datetime.now().strftime("%Y년 %m월 %d일"),
                            font=("굴림", 11),
                            bg=self.colors['panel_bg'],
                            fg=self.colors['text_dim'],
                            anchor=tk.E)
        time_label.pack(side=tk.RIGHT, padx=25, pady=10)
            
    def clear_placeholder(self, event):
        """플레이스홀더 제거"""
        current_text = self.diary_text.get(1.0, tk.END).strip()
        if current_text == "자유롭게 작성해주세요":
            self.diary_text.delete(1.0, tk.END)
            
    def analyze_emotion(self):
        """감정 분석"""
        content = self.diary_text.get(1.0, tk.END).strip()
        
        if not content or content == "자유롭게 작성해주세요":
            messagebox.showwarning("오류", "일기를 작성해주세요")
            return
            
        self.analyze_btn.config(state=tk.DISABLED)
        self.status_label.config(text="분석 중...")
        
        # 백그라운드에서 분석
        thread = threading.Thread(target=self.run_analysis, args=(content,))
        thread.daemon = True
        thread.start()
        
    def run_analysis(self, content):
        """분석 실행"""
        try:
            if HAS_ANALYZER:
                result = analyze_diary_with_custom_model(content)
            else:
                # 시뮬레이션 데이터
                import time
                time.sleep(2)
                result = {
                    'primary_emotion': '기쁨',
                    'secondary_emotions': ['만족', '희망'],
                    'emotion_intensity': 75,
                    'analysis_score': 8,
                    'keywords': ['친구', '즐거움'],
                    'emotion_tags': ['긍정', '사교'],
                    'summary': '전반적으로 긍정적인 감정을 느낀 하루입니다.'
                }
            
            self.root.after(0, self.display_analysis, result)
        except Exception as e:
            self.root.after(0, self.display_error, str(e))
            
    def display_analysis(self, result):
        """분석 결과 표시"""
        self.current_analysis = result
        
        # 결과 제목 업데이트
        self.result_title_label.config(text="감정 분석 완료")
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("━" * 50)
        output.append("감정 분석 결과")
        output.append("━" * 50)
        output.append(f"\n 주된 감정: {result.get('primary_emotion', 'N/A')}")
        output.append(f"\n 보조 감정: {', '.join(result.get('secondary_emotions', []))}")
        output.append(f"\n 감정 강도: {result.get('emotion_intensity', 0)}/100")
        
        # 강도 바
        intensity = result.get('emotion_intensity', 0)
        bar_length = 30
        filled = int((intensity / 100) * bar_length)
        bar = "▰" * filled + "▱" * (bar_length - filled)
        output.append(f"   [{bar}]")
        
        output.append(f"\n 분석 점수: {result.get('analysis_score', 0)}/10")
        output.append(f"\n 주요 키워드: {', '.join(result.get('keywords', []))}")
        output.append(f"\n 감정 태그: {', '.join(result.get('emotion_tags', []))}")
        
        if result.get('summary'):
            output.append(f"\n 한줄 요약:")
            output.append(f"   {result.get('summary')}")
        output.append("\n" + "=" * 60)
        
        self.result_text.insert(tk.END, "\n".join(output))
        self.result_text.config(state=tk.DISABLED)
        
        self.analyze_btn.config(state=tk.NORMAL)
        self.status_label.config(text="분석 완료")
        
    def display_error(self, error):
        """에러 표시"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"분석 오류\n\n{error}")
        self.result_text.config(state=tk.DISABLED)
        
        self.analyze_btn.config(state=tk.NORMAL)
        self.status_label.config(text="[ ERROR OCCURRED ]")
        
    def save_diary(self):
        """일기 저장"""
        content = self.diary_text.get(1.0, tk.END).strip()
        
        if not content or content == "자유롭게 작성해주세요":
            messagebox.showwarning("오류", "일기를 작성해주세요")
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.current_analysis:
                cursor.execute('''
                    INSERT INTO diaries (
                        date, content, primary_emotion, secondary_emotions,
                        emotion_intensity, analysis_score, keywords,
                        emotion_tags, summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    content,
                    self.current_analysis.get('primary_emotion'),
                    json.dumps(self.current_analysis.get('secondary_emotions', []), ensure_ascii=False),
                    self.current_analysis.get('emotion_intensity'),
                    self.current_analysis.get('analysis_score'),
                    json.dumps(self.current_analysis.get('keywords', []), ensure_ascii=False),
                    json.dumps(self.current_analysis.get('emotion_tags', []), ensure_ascii=False),
                    self.current_analysis.get('summary')
                ))
            else:
                cursor.execute('''
                    INSERT INTO diaries (date, content) VALUES (?, ?)
                ''', (date_str, content))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("작성 완료", "일기가 성공적으로 저장되었습니다!\n'내가 쓴 일기'에서 확인하실 수 있습니다.")
            self.status_label.config(text="✓ 저장 완료")
            
            # 저장 후 "내가 쓴 일기" 화면으로 이동
            self.create_ui('history')
            
        except Exception as e:
            messagebox.showerror("저장 오류", f"저장 중 오류가 발생했습니다:\n{e}")
            
    def clear_inputs(self):
        """입력 초기화"""
        self.diary_text.delete(1.0, tk.END)
        self.diary_text.insert(1.0, "자유롭게 작성해주세요")
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.result_title_label.config(text="감정 분석 결과")
        
        self.current_analysis = None
        self.status_label.config(text="초기화 완료")
        
    def load_history(self):
        """기록 불러오기"""
        # 기존 위젯 제거
        for widget in self.history_scrollable.winfo_children():
            widget.destroy()
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, date, content, primary_emotion, summary
                FROM diaries
                ORDER BY created_at DESC
            ''')
            
            diaries = cursor.fetchall()
            conn.close()
            
            if not diaries:
                # 중앙 정렬을 위한 컨테이너
                empty_container = tk.Frame(self.history_scrollable, bg='white')
                empty_container.pack(fill=tk.BOTH, expand=True)
                
                empty_label = tk.Label(empty_container,
                                      text="\n\n저장된 일기가 없습니다.\n일기를 작성하고 저장해보세요!",
                                      font=("굴림", 14),
                                      bg='white',
                                      fg=self.colors['text_dim'],
                                      justify=tk.CENTER)
                empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                for diary in diaries:
                    diary_id, date, content, emotion, summary = diary
                    
                    # 일기 카드
                    card = tk.Frame(self.history_scrollable,
                                   bg=self.colors['panel_bg'],
                                   relief=tk.SOLID,
                                   bd=1)
                    card.pack(fill=tk.X, padx=15, pady=8)
                    
                    # 날짜
                    date_label = tk.Label(card,
                                         text=f"{date}",
                                         font=("굴림", 12, "bold"),
                                         bg=self.colors['panel_bg'],
                                         fg=self.colors['accent'],
                                         anchor=tk.W)
                    date_label.pack(fill=tk.X, padx=18, pady=(12, 6))
                    
                    # 내용 미리보기
                    preview = content[:120] + "..." if len(content) > 120 else content
                    content_label = tk.Label(card,
                                            text=preview,
                                            font=("굴림", 12),
                                            bg=self.colors['panel_bg'],
                                            fg=self.colors['text'],
                                            anchor=tk.W,
                                            justify=tk.LEFT,
                                            wraplength=1200)
                    content_label.pack(fill=tk.X, padx=18, pady=7)
                    
                    # 감정
                    if emotion:
                        emotion_label = tk.Label(card,
                                                text=f"{emotion}",
                                                font=("굴림", 11, "bold"),
                                                bg=self.colors['button_bg'],
                                                fg='white',
                                                padx=14,
                                                pady=5)
                        emotion_label.pack(anchor=tk.W, padx=18, pady=(0, 12))
                        
            self.status_label.config(text="목록 새로고침 완료")
            
        except Exception as e:
            messagebox.showerror("로드 오류", f"기록을 불러오는 중 오류가 발생했습니다:\n{e}")


# ========================================
# MAIN
# ========================================
def main():
    root = tk.Tk()
    app = MoodTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()