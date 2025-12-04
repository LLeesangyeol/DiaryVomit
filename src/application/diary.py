import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading, sys, os

# 상위 폴더 import 허용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ollama 모델 불러오기 여부 확인
try:
    from ollama_analyzer import analyze_diary_with_custom_model
    HAS_ANALYZER = True
except:
    HAS_ANALYZER = False

# DB
from user_db import init_db as init_user_db, login, get_profile, register, ValidationError, UserAlreadyExists
from diary_db import init_db as init_diary_db, save_diary_to_db, get_all_diaries, get_diaries_for_stats


# ================================================================
#                          MAIN CLASS
# ================================================================
class MoodTrackerGUI:
    # ------------------------------------------------------------
    # 초기 설정
    # ------------------------------------------------------------
    def __init__(self, root):
        self.root = root
        self.root.title("감정 분석 일기장")

        # DPI Fix
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # 화면 크기
        w, h = 1400, 900
        self.root.geometry(f"{w}x{h}+{(root.winfo_screenwidth()-w)//2}+{(root.winfo_screenheight()-h)//2}")
        self.root.minsize(1200, 800)

        # UI 색
        self.colors = {
            'bg': '#EBF5FB', 'panel_bg': '#D6EAF8',
            'text': '#1B4F72', 'text_dim': '#5499C7',
            'button_bg': '#5DADE2', 'accent': '#3498DB'
        }
        self.root.configure(bg=self.colors['bg'])

        # DB 초기화
        init_user_db()
        init_diary_db()

        # 전역 상태값
        self.current_analysis = None
        self.main_content = None
        self.current_user = None
        self.current_user_id = None

        self.show_login_screen()

    # ------------------------------------------------------------
    # 로그인 화면
    # ------------------------------------------------------------
    def show_login_screen(self):
        if self.main_content:
            self.main_content.destroy()

        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(self.main_content, bg=self.colors['bg'])
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="로그인", font=("맑은 고딕", 30, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 20))

        # ID
        tk.Label(frame, text="아이디", font=("맑은 고딕", 12),
                 bg=self.colors['bg'], fg=self.colors['text']).pack(anchor=tk.W)
        self.login_id = tk.Entry(frame, font=("맑은 고딕", 13))
        self.login_id.pack(fill=tk.X, pady=6)

        # PW
        tk.Label(frame, text="비밀번호", font=("맑은 고딕", 12),
                 bg=self.colors['bg'], fg=self.colors['text']).pack(anchor=tk.W)
        self.login_pw = tk.Entry(frame, font=("맑은 고딕", 13), show="*")
        self.login_pw.pack(fill=tk.X, pady=6)

        # 로그인 버튼
        tk.Button(frame, text="로그인", font=("맑은 고딕", 13, "bold"),
                  bg=self.colors['accent'], fg='white', relief=tk.FLAT,
                  width=22, pady=12, cursor="hand2",
                  command=self.do_login).pack(pady=(20, 12))

        # 회원가입 버튼
        tk.Button(frame, text="회원가입", font=("맑은 고딕", 11, "bold"),
                  bg=self.colors['button_bg'], fg='white', relief=tk.FLAT,
                  width=22, pady=10, cursor="hand2",
                  command=self.show_register_screen).pack()

    # ------------------------------------------------------------
    # 회원가입 화면
    # ------------------------------------------------------------
    def show_register_screen(self):
        if self.main_content:
            self.main_content.destroy()

        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(self.main_content, bg=self.colors['bg'])
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="회원가입", font=("맑은 고딕", 30, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 20))

        # 입력창들
        labels = [("아이디", "reg_id"), ("비밀번호", "reg_pw"), ("이름", "reg_name")]
        for label, attr in labels:
            tk.Label(frame, text=label, font=("맑은 고딕", 12),
                     bg=self.colors['bg'], fg=self.colors['text']).pack(anchor=tk.W)
            entry = tk.Entry(frame, font=("맑은 고딕", 13), show="*" if attr == "reg_pw" else "")
            entry.pack(fill=tk.X, pady=6)
            setattr(self, attr, entry)

        # 가입 버튼
        tk.Button(frame, text="가입 완료", font=("맑은 고딕", 13, "bold"),
                  bg=self.colors['accent'], fg='white', relief=tk.FLAT,
                  width=22, pady=12, cursor="hand2",
                  command=self.do_register).pack(pady=(20, 12))

        # 로그인 화면으로
        tk.Button(frame, text="로그인 화면으로", font=("맑은 고딕", 11, "bold"),
                  bg=self.colors['button_bg'], fg='white', relief=tk.FLAT,
                  width=22, pady=10, cursor="hand2",
                  command=self.show_login_screen).pack()

    # ------------------------------------------------------------
    # 회원가입 처리
    # ------------------------------------------------------------
    def do_register(self):
        try:
            register(
                self.reg_id.get().strip(),
                self.reg_pw.get().strip(),
                self.reg_name.get().strip()
            )
            messagebox.showinfo("완료", "회원가입이 완료되었습니다!")
            self.show_login_screen()
        except ValidationError as ve:
            messagebox.showwarning("입력 오류", str(ve))
        except UserAlreadyExists as ue:
            messagebox.showwarning("중복 아이디", str(ue))

    # ------------------------------------------------------------
    # 로그인 처리
    # ------------------------------------------------------------
    def do_login(self):
        username = self.login_id.get().strip()
        password = self.login_pw.get().strip()

        ok, msg, user = login(username, password)
        if not ok:
            messagebox.showwarning("로그인 실패", msg)
            return

        profile = get_profile(user)
        self.current_user = profile["username"]
        self.current_user_id = user["id"]

        messagebox.showinfo("환영합니다", f"{self.current_user}님 환영합니다!")
        self.show_menu()

    # ------------------------------------------------------------
    # 메인 메뉴
    # ------------------------------------------------------------
    def show_menu(self):
        if self.main_content:
            self.main_content.destroy()

        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)

        center = tk.Frame(self.main_content, bg=self.colors['bg'])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(center, text="감정 분석 일기장",
                 font=("맑은 고딕", 32, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 10))

        tk.Label(center, text="당신의 감정을 기록하고 분석합니다",
                 font=("맑은 고딕", 14),
                 bg=self.colors['bg'], fg=self.colors['text_dim']).pack(pady=(0, 40))

        bf = tk.Frame(center, bg=self.colors['bg'])
        bf.pack()

        menu_items = [
            ("일기 작성", "write", self.colors['accent']),
            ("주간 감정 통계", "analysis", self.colors['button_bg']),
            ("내가 쓴 일기", "history", self.colors['button_bg'])
        ]

        for text, tab, bg in menu_items:
            tk.Button(bf, text=text,
                      font=("맑은 고딕", 17, "bold"),
                      bg=bg, fg="white", relief=tk.FLAT,
                      width=22, pady=18, cursor="hand2",
                      command=lambda t=tab: self.create_ui(t)).pack(pady=10)

    # ------------------------------------------------------------
    # 공통 UI 래퍼
    # ------------------------------------------------------------
    def create_ui(self, tab):
        if self.main_content:
            self.main_content.destroy()

        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)

        # 헤더
        hdr = tk.Frame(self.main_content, bg=self.colors['accent'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="감정 분석 일기장",
                 font=("맑은 고딕", 20, "bold"),
                 bg=self.colors['accent'], fg="white").pack(side=tk.LEFT, padx=25, pady=18)

        tk.Button(hdr, text="메인 메뉴",
                  font=("맑은 고딕", 12, "bold"),
                  bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, padx=25, pady=12,
                  command=self.show_menu).pack(side=tk.RIGHT, padx=20)

        container = tk.Frame(self.main_content, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # 탭에 따른 화면
        if tab == "write":
            self.create_write(container)
        elif tab == "analysis":
            self.create_analysis(container)
        elif tab == "history":
            self.create_history(container)

        # 상태바
        status = tk.Frame(self.main_content, bg=self.colors['panel_bg'], height=30)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(status, text="준비 완료",
                                     font=("맑은 고딕", 9),
                                     bg=self.colors['panel_bg'], fg=self.colors['text_dim'])
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)

    # ------------------------------------------------------------
    # 일기 작성
    # ------------------------------------------------------------
    def create_write(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True)

        # 버튼 영역
        bf = tk.Frame(frame, bg=self.colors['bg'])
        bf.pack(pady=(0, 15))

        btns = [
            ("감정 분석", self.analyze_emotion, self.colors['button_bg'], True),
            ("작성 완료", self.save_diary, self.colors['accent'], True),
            ("새로 쓰기", self.clear_inputs, self.colors['panel_bg'], False)
        ]
        for text, cmd, bg, white in btns:
            tk.Button(bf, text=text, font=("맑은 고딕", 12, "bold"),
                      bg=bg, fg=('white' if white else self.colors['text']),
                      relief=tk.FLAT, width=14, pady=12,
                      command=cmd).pack(side=tk.LEFT, padx=8)

        # 입력 필드
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill=tk.BOTH, expand=3)

        tk.Label(content, text="오늘의 일기",
                 font=("맑은 고딕", 15, "bold"),
                 bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(0, 10), anchor=tk.W)

        inf = tk.Frame(content, bg="white", relief=tk.SOLID, bd=1)
        inf.pack(fill=tk.BOTH, expand=True)
        self.diary_text = scrolledtext.ScrolledText(
            inf, wrap=tk.WORD,
            font=("맑은 고딕", 11),
            bg="white", fg="#2C3E50",
            relief=tk.FLAT, padx=15, pady=15
        )
        self.diary_text.pack(fill=tk.BOTH, expand=True)
        
        self.diary_text.insert(1.0, "오늘 하루를 기록해주세요...")

        self.result_title = tk.Label(content, text="분석 결과",
                                     font=("맑은 고딕", 15, "bold"),
                                     bg=self.colors['bg'], fg=self.colors['text'])
        self.result_title.pack(pady=(10, 10), anchor=tk.W)

        rf = tk.Frame(content, bg="white", relief=tk.SOLID, bd=1)
        rf.pack(fill=tk.BOTH, expand=True)
        self.result_text = scrolledtext.ScrolledText(
            rf, wrap=tk.WORD,
            font=("맑은 고딕", 10),
            bg="white", fg="#34495E",
            relief=tk.FLAT, padx=15, pady=15,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------
    # 감정 분석
    # ------------------------------------------------------------
    def analyze_emotion(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        if not content or content == "오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
            return
        self.status_label.config(text="분석 중...")
        threading.Thread(target=self.run_analysis, args=(content,), daemon=True).start()

    def run_analysis(self, content):
        try:
            if HAS_ANALYZER:
                result = analyze_diary_with_custom_model(content)
            else:
                # import time
                # time.sleep(2)
                result = {
                    'primary_emotion': '알 수 없음',
                    'secondary_emotions': ['알 수 없음'],
                    'emotion_intensity': 0,
                    'analysis_score': 0,
                    'keywords': ['알 수 없음'],
                    'emotion_tags': ['알 수 없음'],
                    'summary': '알 수 없음'
                }
            self.root.after(0, self.display_analysis, result)
        except Exception as e:
            self.root.after(0, self.display_error, str(e))

    def display_analysis(self, result):
        self.current_analysis = result
        self.result_title.config(text="분석 완료")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)

        out = [
            "=" * 50,
            "감정 분석 결과",
            "=" * 50,
            f"\n주된 감정: {result.get('primary_emotion', 'N/A')}",
            f"보조 감정: {', '.join(result.get('secondary_emotions', []))}",
            f"감정 강도: {result.get('emotion_intensity', 0)}/100"
        ]

        intensity = result.get('emotion_intensity', 0)
        bar = "■" * (intensity // 5) + "□" * (20 - intensity // 5)
        out.append(f"[{bar}]")

        out.extend([
            f"\n분석 점수: {result.get('analysis_score', 0)}/10",
            f"키워드: {', '.join(result.get('keywords', []))}",
            f"태그: {', '.join(result.get('emotion_tags', []))}"
        ])

        if result.get("summary"):
            out.append(f"\n요약: {result['summary']}")

        self.result_text.insert(tk.END, "\n".join(out))
        self.result_text.config(state=tk.DISABLED)
        self.status_label.config(text="분석 완료")

    def display_error(self, error):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"분석 오류\n\n{error}")
        self.result_text.config(state=tk.DISABLED)
        self.status_label.config(text="오류 발생")

    # ------------------------------------------------------------
    # 일기 저장
    # ------------------------------------------------------------
    def save_diary(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        if not content or content == "오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
            return
        try:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_diary_to_db(self.current_user_id, date_str, content, self.current_analysis)
            messagebox.showinfo("완료", "일기가 저장되었습니다")
            self.show_menu()
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패:\n{e}")

    # ------------------------------------------------------------
    # 입력 초기화
    # ------------------------------------------------------------
    def clear_inputs(self):
        self.diary_text.delete(1.0, tk.END)
        self.diary_text.insert(1.0, "오늘 하루를 기록해주세요...")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.result_title.config(text="분석 결과")
        self.current_analysis = None
        self.status_label.config(text="초기화 완료")

    # ------------------------------------------------------------
    # 내가 쓴 일기
    # ------------------------------------------------------------
    def create_history(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="내가 쓴 일기",
                 font=("맑은 고딕", 16, "bold"),
                 bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(0, 15), padx=5, anchor=tk.W)

        # 리스트 영역
        board = tk.Frame(frame, bg='white', relief=tk.SOLID, bd=1)
        board.pack(fill=tk.BOTH, expand=True)

        # 컬럼 헤더
        hdr = tk.Frame(board, bg=self.colors['accent'], height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        for txt, w in [("날짜", 18), ("내용", 0), ("감정", 12)]:
            tk.Label(hdr, text=txt, width=w,
                     font=("맑은 고딕", 11, "bold"),
                     bg=self.colors['accent'], fg='white',
                     anchor=(tk.W if txt == "날짜" else tk.CENTER)
                     ).pack(side=tk.LEFT, fill=(tk.X if txt == "내용" else None), expand=(txt == "내용"), padx=10)

        # 스크롤 캔버스
        lf = tk.Frame(board, bg='white')
        lf.pack(fill=tk.BOTH, expand=True)

        self.history_canvas = tk.Canvas(lf, bg='white', highlightthickness=0)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.history_canvas.yview)

        self.history_scrollable = tk.Frame(self.history_canvas, bg='white')
        frame_id = self.history_canvas.create_window((0, 0), window=self.history_scrollable, anchor="nw")

        self.history_scrollable.bind("<Configure>",
                                     lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        self.history_canvas.bind("<Configure>",
                                 lambda e: self.history_canvas.itemconfig(frame_id, width=e.width))

        self.history_canvas.configure(yscrollcommand=sb.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tk.Button(frame, text="새로고침",
                  font=("맑은 고딕", 12, "bold"),
                  bg=self.colors['button_bg'], fg='white',
                  relief=tk.FLAT, width=16, pady=10,
                  command=self.load_history).pack(pady=8)

        self.load_history()

    def load_history(self):
        for w in self.history_scrollable.winfo_children():
            w.destroy()

        try:
            diaries = get_all_diaries(self.current_user_id)

            if not diaries:
                empty = tk.Label(self.history_scrollable, text="저장된 일기가 없습니다",
                                 font=("맑은 고딕", 12), bg='white',
                                 fg=self.colors['text_dim'])
                empty.pack(pady=50)
                return

            for idx, (date, content, emotion) in enumerate(diaries):
                bg = ('white' if idx % 2 == 0 else self.colors['bg'])
                row = tk.Frame(self.history_scrollable, bg=bg, height=40)
                row.pack(fill=tk.X)
                row.pack_propagate(False)

                tk.Label(row, text=date.split()[0], width=18,
                         font=("맑은 고딕", 10),
                         bg=bg, fg=self.colors['text'], anchor=tk.W).pack(side=tk.LEFT, padx=12)

                preview = content[:50] + "..." if len(content) > 50 else content
                tk.Label(row, text=preview,
                         font=("맑은 고딕", 10),
                         bg=bg, fg=self.colors['text'],
                         anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

                tk.Label(row, text=emotion if emotion else "-",
                         font=("맑은 고딕", 10, "bold"),
                         bg=(self.colors['button_bg'] if emotion else bg),
                         fg=('white' if emotion else self.colors['text_dim']),
                         width=12).pack(side=tk.LEFT, padx=10)

                if getattr(self, "status_label", None) and self.status_label.winfo_exists():
                    self.status_label.config(text="목록 로드 완료")



        except Exception as e:
            messagebox.showerror("오류", f"로드 실패:\n{e}")

    # ------------------------------------------------------------
    # 주간 통계
    # ------------------------------------------------------------
    def create_analysis(self, parent):
        self.analysis_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        self.load_stats()

    def load_stats(self):
        try:
            all_diaries, emo_sum = get_diaries_for_stats(self.current_user_id)
            total = len(all_diaries)

            # 스크롤용 컨테이너
            sf = tk.Frame(self.analysis_frame, bg='white', relief=tk.SOLID, bd=1)
            sf.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(sf, bg='white', highlightthickness=0)
            sb = ttk.Scrollbar(sf, orient="vertical", command=canvas.yview)

            scrollable = tk.Frame(canvas, bg='white')
            frame_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")

            scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(frame_id, width=e.width))

            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")

            if total == 0:
                tk.Label(scrollable, text="작성된 일기가 없습니다",
                         font=("맑은 고딕", 12), bg='white',
                         fg=self.colors['text_dim']).pack(pady=40)
                return

            # 상단 요약 카드
            hdr = tk.Frame(scrollable, bg=self.colors['accent'], height=100)
            hdr.pack(fill=tk.X)
            hdr.pack_propagate(False)

            stats = tk.Frame(hdr, bg=self.colors['accent'])
            stats.pack(expand=True, fill=tk.X)
            stats.columnconfigure((0, 1, 2), weight=1)

            items = [
                ("총 일기 수", f"{total}개"),
                ("분석 주차", f"{(total + 6) // 7}주"),
                ("주요 감정", emo_sum[0][0] if emo_sum else "-")
            ]

            for idx, (lbl, val) in enumerate(items):
                c = tk.Frame(stats, bg='white', height=80)
                c.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")
                c.pack_propagate(False)

                tk.Label(c, text=lbl, font=("맑은 고딕", 14),
                         bg='white', fg=self.colors['text_dim']).pack(pady=(5, 2))
                tk.Label(c, text=val, font=("맑은 고딕", 24, "bold"),
                         bg='white', fg=self.colors['accent']).pack()

            # 주간 분석
            for i in range(0, len(all_diaries), 7):
                week = all_diaries[i:i + 7]

                emotions = {}
                total_int = 0
                for _, date, emo, intensity in week:
                    if emo:
                        emotions[emo] = emotions.get(emo, 0) + 1
                        if intensity:
                            total_int += intensity

                if not emotions:
                    continue

                most = max(emotions.items(), key=lambda x: x[1])[0]
                avg_int = total_int / len(week)

                card = tk.Frame(scrollable, bg=self.colors['panel_bg'])
                card.pack(fill=tk.X, padx=15, pady=10)

                # 헤더
                h = tk.Frame(card, bg=self.colors['accent'], height=60)
                h.pack(fill=tk.X)
                h.pack_propagate(False)

                hc = tk.Frame(h, bg=self.colors['accent'])
                hc.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

                tk.Label(hc, text=f"Week {(i // 7) + 1}",
                         font=("맑은 고딕", 15, "bold"),
                         bg=self.colors['accent'], fg='white').pack(side=tk.LEFT)

                tk.Label(hc,
                         text=f"{week[-1][1].split()[0]} ~ {week[0][1].split()[0]}  |  {len(week)}개",
                         font=("맑은 고딕", 12),
                         bg=self.colors['accent'], fg='white').pack(side=tk.LEFT, padx=20)

                tk.Label(hc, text=f"주요: {most}",
                         font=("맑은 고딕", 14, "bold"),
                         bg='white', fg=self.colors['button_bg'],
                         padx=18, pady=6).pack(side=tk.RIGHT)

                # 감정별 차트
                chart = tk.Frame(card, bg='white')
                chart.pack(fill=tk.X)

                max_cnt = max(emotions.values())
                for emo, cnt in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
                    row = tk.Frame(chart, bg='white')
                    row.pack(fill=tk.X, padx=20, pady=5)

                    tk.Label(row, text=emo,
                             font=("맑은 고딕", 14, "bold"),
                             bg=self.colors['button_bg'], fg='white',
                             width=8).pack(side=tk.LEFT, padx=10)

                    tk.Label(row, text=f"{cnt}회",
                             font=("맑은 고딕", 12),
                             bg='white', width=5).pack(side=tk.LEFT)

                    bar_bg = tk.Frame(row, bg='#E8E8E8', height=28)
                    bar_bg.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=15)

                    bar = tk.Frame(bar_bg, bg=self.colors['accent'], height=28)
                    bar.place(relx=0, rely=0, relwidth=cnt / max_cnt, relheight=1)

                    tk.Label(row, text=f"{(cnt / len(week)) * 100:.0f}%",
                             font=("맑은 고딕", 12, "bold"),
                             bg='white', fg=self.colors['accent'], width=5).pack(side=tk.LEFT)

            
            if getattr(self, "status_label", None) and self.status_label.winfo_exists():
                self.status_label.config(text="목록 로드 완료")


        except Exception as e:
            messagebox.showerror("오류", f"통계 로드 실패:\n{e}")


# ================================================================
#                         프로그램 실행
# ================================================================
def main():
    root = tk.Tk()
    app = MoodTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
