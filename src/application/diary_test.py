#!/usr/bin/env python3
# coding: utf-8

"""
MOOD TRACKER v1.0 - AI EMOTION ANALYSIS
감정 분석 기반 일기 추적
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

# 데이터베이스 설정
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

class MoodTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("감정 분석 일기장")
        
        # DPI 인식 설정
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 화면 크기 설정
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1400
        window_height = 900
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 800)
        
        # 색상 테마
        self.colors = {
            'bg': '#EBF5FB',
            'panel_bg': '#D6EAF8',
            'text': '#1B4F72',
            'text_dim': '#5499C7',
            'button_bg': '#5DADE2',
            'accent': '#3498DB'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        init_database()
        
        self.current_analysis = None
        self.main_content = None
        
        self.show_menu()
        
    def show_menu(self):
        """메뉴 화면"""
        if self.main_content:
            self.main_content.destroy()
        
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        center_frame = tk.Frame(self.main_content, bg=self.colors['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(center_frame,
                text="감정 분석 일기장",
                font=("맑은 고딕", 32, "bold"),
                bg=self.colors['bg'],
                fg=self.colors['accent']).pack(pady=(0, 10))
        
        tk.Label(center_frame,
                text="당신의 감정을 기록하고 분석합니다",
                font=("맑은 고딕", 14),
                bg=self.colors['bg'],
                fg=self.colors['text_dim']).pack(pady=(0, 40))
        
        button_frame = tk.Frame(center_frame, bg=self.colors['bg'])
        button_frame.pack()
        
        for text, command in [
            ("일기 작성", lambda: self.create_ui('write')),
            ("주간 감정 통계", lambda: self.create_ui('analysis')),
            ("내가 쓴 일기", lambda: self.create_ui('history'))
        ]:
            tk.Button(button_frame,
                     text=text,
                     font=("맑은 고딕", 16, "bold"),
                     bg=self.colors['accent'] if text == "일기 작성" else self.colors['button_bg'],
                     fg='white',
                     activebackground='#2980B9',
                     activeforeground='white',
                     relief=tk.FLAT,
                     bd=0,
                     width=20,
                     pady=15,
                     cursor="hand2",
                     command=command).pack(pady=8)
    
    def create_ui(self, tab='write'):
        """메인 UI 생성"""
        if self.main_content:
            self.main_content.destroy()
        
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        self.create_header()
        
        tab_container = tk.Frame(self.main_content, bg=self.colors['bg'])
        tab_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)
        
        if tab == 'write':
            self.create_write_content(tab_container)
        elif tab == 'analysis':
            self.create_analysis_content(tab_container)
        elif tab == 'history':
            self.create_history_content(tab_container)
            self.load_history()
        
        self.create_statusbar()
        
    def create_header(self):
        """헤더"""
        header = tk.Frame(self.main_content, bg=self.colors['accent'])
        header.pack(fill=tk.X)
        
        content = tk.Frame(header, bg=self.colors['accent'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        tk.Label(content,
                text="감정 분석 일기장",
                font=("맑은 고딕", 18, "bold"),
                bg=self.colors['accent'],
                fg='white').pack(anchor=tk.W)
        
        tk.Button(header,
                 text="메인 메뉴",
                 font=("맑은 고딕", 11, "bold"),
                 bg=self.colors['accent'],
                 fg='white',
                 activebackground='#2980B9',
                 relief=tk.FLAT,
                 bd=0,
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.show_menu).pack(side=tk.RIGHT, padx=15)
        
    def create_write_content(self, parent):
        """일기 작성"""
        self.write_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.write_frame.pack(fill=tk.BOTH, expand=True)
        
        # 버튼 (상단 배치)
        button_frame = tk.Frame(self.write_frame, bg=self.colors['bg'])
        button_frame.pack(pady=(0, 12))
        
        btn1 = tk.Button(button_frame,
                     text="감정 분석",
                     font=("맑은 고딕", 11, "bold"),
                     bg=self.colors['button_bg'],
                     fg='white',
                     activebackground=self.colors['accent'],
                     relief=tk.FLAT,
                     bd=0,
                     width=12,
                     pady=10,
                     cursor="hand2",
                     command=self.analyze_emotion)
        btn1.pack(side=tk.LEFT, padx=6)
        
        btn2 = tk.Button(button_frame,
                     text="작성 완료",
                     font=("맑은 고딕", 11, "bold"),
                     bg=self.colors['accent'],
                     fg='white',
                     activebackground=self.colors['accent'],
                     relief=tk.FLAT,
                     bd=0,
                     width=12,
                     pady=10,
                     cursor="hand2",
                     command=self.save_diary)
        btn2.pack(side=tk.LEFT, padx=6)
        
        btn3 = tk.Button(button_frame,
                     text="새로 쓰기",
                     font=("맑은 고딕", 11, "bold"),
                     bg=self.colors['panel_bg'],
                     fg=self.colors['text'],
                     activebackground=self.colors['accent'],
                     relief=tk.FLAT,
                     bd=0,
                     width=12,
                     pady=10,
                     cursor="hand2",
                     command=self.clear_inputs)
        btn3.pack(side=tk.LEFT, padx=6)
        
        content_area = tk.Frame(self.write_frame, bg=self.colors['bg'])
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # 입력 영역
        input_section = tk.Frame(content_area, bg=self.colors['bg'])
        input_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        input_label = tk.Label(input_section,
                text="오늘의 일기",
                font=("맑은 고딕", 13, "bold"),
                bg=self.colors['bg'],
                fg=self.colors['text'])
        input_label.pack(pady=(0, 8), anchor=tk.W)
        
        input_frame = tk.Frame(input_section, bg='white', relief=tk.SOLID, bd=1)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        self.diary_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("맑은 고딕", 11),
            bg='white',
            fg='#2C3E50',
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.diary_text.pack(fill=tk.BOTH, expand=True)
        self.diary_text.insert(1.0, "오늘 하루를 기록해주세요...")
        self.diary_text.bind("<FocusIn>", self.clear_placeholder)
        
        # 결과 영역
        result_section = tk.Frame(content_area, bg=self.colors['bg'])
        result_section.pack(fill=tk.BOTH, expand=True)
        
        self.result_title = tk.Label(result_section,
                text="분석 결과",
                font=("맑은 고딕", 13, "bold"),
                bg=self.colors['bg'],
                fg=self.colors['text'])
        self.result_title.pack(pady=(0, 8), anchor=tk.W)
        
        result_frame = tk.Frame(result_section, bg='white', relief=tk.SOLID, bd=1)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("맑은 고딕", 10),
            bg='white',
            fg='#34495E',
            relief=tk.FLAT,
            padx=15,
            pady=15,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
    def create_analysis_content(self, parent):
        """감정 통계"""
        self.analysis_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(self.analysis_frame,
                text="주간 감정 통계",
                font=("맑은 고딕", 13, "bold"),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(pady=(0, 15), anchor=tk.W, padx=5)
        
        self.load_emotion_statistics()
        
    def create_history_content(self, parent):
        """일기 목록"""
        self.history_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.history_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(self.history_frame,
                text="내가 쓴 일기",
                font=("맑은 고딕", 13, "bold"),
                bg=self.colors['bg'],
                fg=self.colors['text'])
        title_label.pack(pady=(0, 12), anchor=tk.W, padx=5)
        
        board_frame = tk.Frame(self.history_frame, bg='white', relief=tk.SOLID, bd=1)
        board_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # 헤더
        header = tk.Frame(board_frame, bg=self.colors['accent'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="날짜", font=("맑은 고딕", 11, "bold"),
                bg=self.colors['accent'], fg='white', width=18, anchor=tk.W).pack(side=tk.LEFT, padx=15)
        tk.Label(header, text="내용", font=("맑은 고딕", 11, "bold"),
                bg=self.colors['accent'], fg='white').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Label(header, text="감정", font=("맑은 고딕", 11, "bold"),
                bg=self.colors['accent'], fg='white', width=12).pack(side=tk.LEFT, padx=15)
        
        # 스크롤
        list_frame = tk.Frame(board_frame, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_canvas.yview)
        
        self.history_scrollable = tk.Frame(self.history_canvas, bg='white')
        self.history_scrollable.bind("<Configure>",
                                     lambda e: self.history_canvas.configure(
                                         scrollregion=self.history_canvas.bbox("all")))
        
        self.history_canvas.create_window((0, 0), window=self.history_scrollable, anchor="nw")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        refresh_btn = tk.Button(self.history_frame,
                 text="새로고침",
                 font=("맑은 고딕", 11, "bold"),
                 bg=self.colors['button_bg'],
                 fg='white',
                 relief=tk.FLAT,
                 bd=0,
                 width=15,
                 pady=10,
                 cursor="hand2",
                 command=self.load_history)
        refresh_btn.pack()
        
        # 화면 진입 시 자동 로드
        self.load_history()
        
    def create_statusbar(self):
        """상태바"""
        status = tk.Frame(self.main_content, bg=self.colors['panel_bg'], height=30)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status,
                                     text="준비 완료",
                                     font=("맑은 고딕", 9),
                                     bg=self.colors['panel_bg'],
                                     fg=self.colors['text_dim'])
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)
        
        tk.Label(status,
                text=datetime.now().strftime("%Y년 %m월 %d일"),
                font=("맑은 고딕", 9),
                bg=self.colors['panel_bg'],
                fg=self.colors['text_dim']).pack(side=tk.RIGHT, padx=20, pady=8)
    
    def clear_placeholder(self, event):
        text = self.diary_text.get(1.0, tk.END).strip()
        if text == "오늘 하루를 기록해주세요...":
            self.diary_text.delete(1.0, tk.END)
    
    def analyze_emotion(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        
        if not content or content == "오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
            return
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text="분석 중...")
        
        thread = threading.Thread(target=self.run_analysis, args=(content,))
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, content):
        try:
            if HAS_ANALYZER:
                result = analyze_diary_with_custom_model(content)
            else:
                import time
                time.sleep(2)
                result = {
                    'primary_emotion': '기쁨',
                    'secondary_emotions': ['만족', '희망'],
                    'emotion_intensity': 75,
                    'analysis_score': 8,
                    'keywords': ['친구', '즐거움'],
                    'emotion_tags': ['긍정', '사교'],
                    'summary': '전반적으로 긍정적인 하루였습니다.'
                }
            
            self.root.after(0, self.display_analysis, result)
        except Exception as e:
            self.root.after(0, self.display_error, str(e))
    
    def display_analysis(self, result):
        self.current_analysis = result
        self.result_title.config(text="분석 완료")
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 50)
        output.append("감정 분석 결과")
        output.append("=" * 50)
        output.append(f"\n주된 감정: {result.get('primary_emotion', 'N/A')}")
        output.append(f"보조 감정: {', '.join(result.get('secondary_emotions', []))}")
        output.append(f"감정 강도: {result.get('emotion_intensity', 0)}/100")
        
        intensity = result.get('emotion_intensity', 0)
        bar = "■" * (intensity // 5) + "□" * (20 - intensity // 5)
        output.append(f"[{bar}]")
        
        output.append(f"\n분석 점수: {result.get('analysis_score', 0)}/10")
        output.append(f"키워드: {', '.join(result.get('keywords', []))}")
        output.append(f"태그: {', '.join(result.get('emotion_tags', []))}")
        
        if result.get('summary'):
            output.append(f"\n요약: {result.get('summary')}")
        
        self.result_text.insert(tk.END, "\n".join(output))
        self.result_text.config(state=tk.DISABLED)
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text="분석 완료")
    
    def display_error(self, error):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"분석 오류\n\n{error}")
        self.result_text.config(state=tk.DISABLED)
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text="오류 발생")
    
    def save_diary(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        
        if not content or content == "오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
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
                cursor.execute('INSERT INTO diaries (date, content) VALUES (?, ?)', (date_str, content))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("완료", "일기가 저장되었습니다")
            self.show_menu()
            
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패:\n{e}")
    
    def clear_inputs(self):
        self.diary_text.delete(1.0, tk.END)
        self.diary_text.insert(1.0, "오늘 하루를 기록해주세요...")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        if hasattr(self, 'result_title'):
            self.result_title.config(text="분석 결과")
        
        self.current_analysis = None
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text="초기화 완료")
    
    def load_history(self):
        for widget in self.history_scrollable.winfo_children():
            widget.destroy()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT date, content, primary_emotion FROM diaries ORDER BY created_at DESC')
            diaries = cursor.fetchall()
            conn.close()
            
            if not diaries:
                empty = tk.Frame(self.history_scrollable, bg='white')
                empty.pack(fill=tk.BOTH, expand=True)
                tk.Label(empty,
                        text="저장된 일기가 없습니다",
                        font=("맑은 고딕", 12),
                        bg='white',
                        fg=self.colors['text_dim']).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                for idx, (date, content, emotion) in enumerate(diaries):
                    row_bg = 'white' if idx % 2 == 0 else self.colors['bg']
                    row = tk.Frame(self.history_scrollable, bg=row_bg, height=45)
                    row.pack(fill=tk.X)
                    row.pack_propagate(False)
                    
                    tk.Label(row,
                            text=date.split()[0],
                            font=("맑은 고딕", 10),
                            bg=row_bg,
                            fg=self.colors['text'],
                            width=18,
                            anchor=tk.W).pack(side=tk.LEFT, padx=15)
                    
                    preview = content[:50] + "..." if len(content) > 50 else content
                    tk.Label(row,
                            text=preview,
                            font=("맑은 고딕", 10),
                            bg=row_bg,
                            fg=self.colors['text'],
                            anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
                    
                    tk.Label(row,
                            text=emotion if emotion else "-",
                            font=("맑은 고딕", 10, "bold"),
                            bg=self.colors['button_bg'] if emotion else row_bg,
                            fg='white' if emotion else self.colors['text_dim'],
                            width=12).pack(side=tk.LEFT, padx=15)
            
            if hasattr(self, 'status_label'):
                self.status_label.config(text="목록 로드 완료")
        except Exception as e:
            messagebox.showerror("오류", f"로드 실패:\n{e}")
    
    def load_emotion_statistics(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, date, primary_emotion, emotion_intensity FROM diaries ORDER BY created_at DESC')
            all_diaries = cursor.fetchall()
            total = len(all_diaries)
            
            # 7개씩 묶어서 주간 데이터
            weekly_groups = []
            for i in range(0, len(all_diaries), 7):
                week_diaries = all_diaries[i:i+7]
                emotions = {}
                total_intensity = 0
                
                for _, date, emotion, intensity in week_diaries:
                    if emotion:
                        emotions[emotion] = emotions.get(emotion, 0) + 1
                        if intensity:
                            total_intensity += intensity
                
                if emotions:
                    most_common = max(emotions.items(), key=lambda x: x[1])[0]
                    avg_intensity = total_intensity / len(week_diaries) if total_intensity > 0 else 0
                    weekly_groups.append({
                        'week_num': len(weekly_groups) + 1,
                        'count': len(week_diaries),
                        'emotions': emotions,
                        'most_common': most_common,
                        'avg_intensity': avg_intensity,
                        'dates': f"{week_diaries[-1][1].split()[0]} ~ {week_diaries[0][1].split()[0]}"
                    })
            
            cursor.execute('''
                SELECT primary_emotion, COUNT(*), AVG(emotion_intensity)
                FROM diaries WHERE primary_emotion IS NOT NULL
                GROUP BY primary_emotion ORDER BY COUNT(*) DESC
            ''')
            emotion_summary = cursor.fetchall()
            conn.close()
            
            # UI 생성
            stats_frame = tk.Frame(self.analysis_frame, bg='white', relief=tk.SOLID, bd=1)
            stats_frame.pack(fill=tk.BOTH, expand=True)
            
            canvas = tk.Canvas(stats_frame, bg='white', highlightthickness=0)
            scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=canvas.yview)
            scrollable = tk.Frame(canvas, bg='white')
            
            scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            if total == 0:
                empty = tk.Frame(scrollable, bg='white')
                empty.pack(fill=tk.BOTH, expand=True)
                tk.Label(empty,
                        text="작성된 일기가 없습니다",
                        font=("맑은 고딕", 12),
                        bg='white',
                        fg=self.colors['text_dim']).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                # 대시보드 헤더
                header = tk.Frame(scrollable, bg=self.colors['accent'], height=70)
                header.pack(fill=tk.X, padx=15, pady=(15, 0))
                header.pack_propagate(False)
                
                stats = tk.Frame(header, bg=self.colors['accent'])
                stats.pack(expand=True)
                
                for label, value in [
                    ("총 일기", f"{total}개"),
                    ("분석 주차", f"{len(weekly_groups)}주"),
                    ("주요 감정", emotion_summary[0][0] if emotion_summary else "-")
                ]:
                    card = tk.Frame(stats, bg='white', width=180, height=50)
                    card.pack(side=tk.LEFT, padx=8)
                    card.pack_propagate(False)
                    tk.Label(card, text=label, font=("맑은 고딕", 9), bg='white', fg=self.colors['text_dim']).pack(pady=(8, 0))
                    tk.Label(card, text=value, font=("맑은 고딕", 14, "bold"), bg='white', fg=self.colors['accent']).pack()
                
                # 주간 통계
                if weekly_groups:
                    week_section = tk.Frame(scrollable, bg='white')
                    week_section.pack(fill=tk.BOTH, padx=15, pady=15)
                    
                    tk.Label(week_section,
                            text="주간 감정 분석 (일기 7개 단위)",
                            font=("맑은 고딕", 12, "bold"),
                            bg='white',
                            fg=self.colors['text']).pack(pady=(5, 10), anchor=tk.W)
                    
                    for week_data in weekly_groups:
                        card = tk.Frame(week_section, bg=self.colors['panel_bg'], relief=tk.SOLID, bd=1)
                        card.pack(fill=tk.X, pady=8)
                        
                        # 헤더
                        h = tk.Frame(card, bg=self.colors['accent'], height=45)
                        h.pack(fill=tk.X)
                        h.pack_propagate(False)
                        
                        hc = tk.Frame(h, bg=self.colors['accent'])
                        hc.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
                        
                        tk.Label(hc,
                                text=f"Week {week_data['week_num']}",
                                font=("맑은 고딕", 11, "bold"),
                                bg=self.colors['accent'],
                                fg='white').pack(side=tk.LEFT)
                        
                        tk.Label(hc,
                                text=f"{week_data['dates']}  |  {week_data['count']}개",
                                font=("맑은 고딕", 9),
                                bg=self.colors['accent'],
                                fg='white').pack(side=tk.LEFT, padx=15)
                        
                        tk.Label(hc,
                                text=f"주요: {week_data['most_common']}",
                                font=("맑은 고딕", 10, "bold"),
                                bg='white',
                                fg=self.colors['button_bg'],
                                padx=12,
                                pady=4).pack(side=tk.RIGHT)
                        
                        # 차트
                        chart = tk.Frame(card, bg='white', relief=tk.SOLID, bd=1)
                        chart.pack(fill=tk.X, padx=15, pady=12)
                        
                        max_cnt = max(week_data['emotions'].values())
                        for emotion, count in sorted(week_data['emotions'].items(), key=lambda x: x[1], reverse=True):
                            row = tk.Frame(chart, bg='white')
                            row.pack(fill=tk.X, padx=12, pady=6)
                            
                            tk.Label(row,
                                    text=emotion,
                                    font=("맑은 고딕", 10, "bold"),
                                    bg=self.colors['button_bg'],
                                    fg='white',
                                    width=8,
                                    padx=6,
                                    pady=3).pack(side=tk.LEFT, padx=(0, 8))
                            
                            tk.Label(row,
                                    text=f"{count}회",
                                    font=("맑은 고딕", 10),
                                    bg='white',
                                    width=6,
                                    anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
                            
                            bar_bg = tk.Frame(row, bg='#E8E8E8', height=20)
                            bar_bg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
                            
                            bar = tk.Frame(bar_bg, bg=self.colors['accent'], height=20)
                            bar.place(relx=0, rely=0, relwidth=count/max_cnt, relheight=1)
                            
                            pct = (count / week_data['count']) * 100
                            tk.Label(row,
                                    text=f"{pct:.0f}%",
                                    font=("맑은 고딕", 9, "bold"),
                                    bg='white',
                                    fg=self.colors['accent'],
                                    width=5).pack(side=tk.LEFT)
                        
                        # 강도 바
                        if week_data['avg_intensity'] > 0:
                            intensity_f = tk.Frame(card, bg=self.colors['panel_bg'])
                            intensity_f.pack(fill=tk.X, padx=15, pady=(0, 12))
                            
                            tk.Label(intensity_f,
                                    text=f"평균 강도: {week_data['avg_intensity']:.1f}/100",
                                    font=("맑은 고딕", 10),
                                    bg=self.colors['panel_bg'],
                                    fg=self.colors['text']).pack(anchor=tk.W)
                            
                            bar_frame = tk.Frame(intensity_f, bg='#E8E8E8', height=12)
                            bar_frame.pack(fill=tk.X, pady=(4, 0))
                            
                            bar = tk.Frame(bar_frame, bg=self.colors['button_bg'], height=12)
                            bar.place(relx=0, rely=0, relwidth=week_data['avg_intensity']/100, relheight=1)
        
        except Exception as e:
            tk.Label(self.analysis_frame,
                    text=f"통계 로드 오류:\n{e}",
                    font=("맑은 고딕", 11),
                    bg=self.colors['bg'],
                    fg='red').pack(expand=True)

def main():
    root = tk.Tk()
    app = MoodTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
