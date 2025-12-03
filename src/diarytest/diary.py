import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading, sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from ollama_analyzer import analyze_diary_with_custom_model
    HAS_ANALYZER = True
except: HAS_ANALYZER = False

from diary_db import init_db, save_diary_to_db, get_all_diaries, get_diaries_for_stats, register_user, login_user, ValidationError, UserAlreadyExists

class MoodTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("감정 분석 일기장")
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except: pass
        
        w, h = 1500, 1100
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        
        if y < 0: y = 0
        if x < 0: x = 0
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1200, 800)
        
        self.colors = {'bg':'#EBF5FB','panel_bg':'#D6EAF8','text':'#1B4F72','text_dim':'#5499C7','button_bg':'#5DADE2','accent':'#3498DB'}
        self.root.configure(bg=self.colors['bg'])
        self.user_id = None
        init_db()
        self.current_analysis = None
        self.main_content = None
        self.show_login()
    
    def show_login(self):
        """로그인 화면"""
        if self.main_content: self.main_content.destroy()
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        center = tk.Frame(self.main_content, bg=self.colors['bg'])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(center, text="감정 분석 일기장", font=("맑은 고딕", 42, "bold"), 
                bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 15))

        input_frame = tk.Frame(center, bg=self.colors['bg'])
        input_frame.pack(pady=30)
        
        tk.Label(input_frame, text="아이디", font=("맑은 고딕", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['text'], width=10).grid(row=0, column=0, sticky=tk.E, pady=15, padx=15)
        self.login_username = tk.Entry(input_frame, font=("맑은 고딕", 16), width=30, relief=tk.SOLID, bd=2)
        self.login_username.grid(row=0, column=1, pady=15, padx=15)
        
        tk.Label(input_frame, text="비밀번호", font=("맑은 고딕", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['text'], width=10).grid(row=1, column=0, sticky=tk.E, pady=15, padx=15)
        self.login_password = tk.Entry(input_frame, font=("맑은 고딕", 16), width=30, show="●", relief=tk.SOLID, bd=2)
        self.login_password.grid(row=1, column=1, pady=15, padx=15)
        self.login_password.bind('<Return>', lambda e: self.do_login())

        btn_frame = tk.Frame(center, bg=self.colors['bg'])
        btn_frame.pack(pady=40)
        
        login_btn = tk.Button(btn_frame, text="로그인", font=("맑은 고딕", 18, "bold"), 
                             bg=self.colors['accent'], fg='white', relief=tk.FLAT, 
                             width=15, pady=15, cursor="hand2", command=self.do_login, 
                             activebackground='#2980B9', bd=0)
        login_btn.pack(side=tk.LEFT, padx=10)
        
        register_btn = tk.Button(btn_frame, text="회원가입", font=("맑은 고딕", 18, "bold"), 
                                bg=self.colors['button_bg'], fg='white', relief=tk.FLAT, 
                                width=15, pady=15, cursor="hand2", command=self.show_register, 
                                activebackground='#2980B9', bd=0)
        register_btn.pack(side=tk.LEFT, padx=10)
    
    def show_register(self):
        """회원가입 화면"""
        if self.main_content: self.main_content.destroy()
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        center = tk.Frame(self.main_content, bg=self.colors['bg'])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(center, text="회원가입", font=("맑은 고딕", 42, "bold"), 
                bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0, 15))
        tk.Label(center, text="새 계정을 만들어주세요", font=("맑은 고딕", 16), 
                bg=self.colors['bg'], fg=self.colors['text_dim']).pack(pady=(0, 50))

        input_frame = tk.Frame(center, bg=self.colors['bg'])
        input_frame.pack(pady=30)
        
        tk.Label(input_frame, text="아이디", font=("맑은 고딕", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['text'], width=12).grid(row=0, column=0, sticky=tk.E, pady=15, padx=15)
        self.reg_username = tk.Entry(input_frame, font=("맑은 고딕", 16), width=25, relief=tk.SOLID, bd=2)
        self.reg_username.grid(row=0, column=1, pady=15, padx=15)
        tk.Label(input_frame, text="3자 이상", font=("맑은 고딕", 11), 
                bg=self.colors['bg'], fg=self.colors['text_dim']).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        tk.Label(input_frame, text="비밀번호", font=("맑은 고딕", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['text'], width=12).grid(row=1, column=0, sticky=tk.E, pady=15, padx=15)
        self.reg_password = tk.Entry(input_frame, font=("맑은 고딕", 16), width=25, show="●", relief=tk.SOLID, bd=2)
        self.reg_password.grid(row=1, column=1, pady=15, padx=15)
        tk.Label(input_frame, text="4자 이상", font=("맑은 고딕", 11), 
                bg=self.colors['bg'], fg=self.colors['text_dim']).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        tk.Label(input_frame, text="비밀번호 확인", font=("맑은 고딕", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['text'], width=12).grid(row=2, column=0, sticky=tk.E, pady=15, padx=15)
        self.reg_password_confirm = tk.Entry(input_frame, font=("맑은 고딕", 16), width=25, show="●", relief=tk.SOLID, bd=2)
        self.reg_password_confirm.grid(row=2, column=1, pady=15, padx=15)
        self.reg_password_confirm.bind('<Return>', lambda e: self.do_register())
        
        btn_frame = tk.Frame(center, bg=self.colors['bg'])
        btn_frame.pack(pady=40)
        
        register_btn = tk.Button(btn_frame, text="가입하기", font=("맑은 고딕", 18, "bold"), 
                                bg=self.colors['accent'], fg='white', relief=tk.FLAT, 
                                width=15, pady=15, cursor="hand2", command=self.do_register, 
                                activebackground='#2980B9', bd=0)
        register_btn.pack(side=tk.LEFT, padx=10)
        
        back_btn = tk.Button(btn_frame, text="로그인으로", font=("맑은 고딕", 18, "bold"), 
                            bg=self.colors['button_bg'], fg='white', relief=tk.FLAT, 
                            width=15, pady=15, cursor="hand2", command=self.show_login, 
                            activebackground='#2980B9', bd=0)
        back_btn.pack(side=tk.LEFT, padx=10)
    
    def do_login(self):
        """로그인 처리"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        try:
            user_id = login_user(username, password)
            self.user_id = user_id
            messagebox.showinfo("로그인", f"{username}님, 환영합니다")
            self.show_menu()
        except ValidationError as e:
            messagebox.showerror("로그인 실패", str(e))
        except Exception as e:
            messagebox.showerror("오류", f"로그인 중 오류 발생:\n{e}")
    
    def do_register(self):
        """회원가입 처리"""
        username = self.reg_username.get().strip()
        password = self.reg_password.get()
        password_confirm = self.reg_password_confirm.get()
        
        if password != password_confirm:
            messagebox.showerror("오류", "비밀번호가 일치하지 않습니다")
            return
        
        try:
            register_user(username, password)
            messagebox.showinfo("가입 완료", "회원가입이 완료되었습니다!\n로그인 해주세요.")
            self.show_login()
        except ValidationError as e:
            messagebox.showerror("가입 실패", str(e))
        except UserAlreadyExists as e:
            messagebox.showerror("가입 실패", str(e))
        except Exception as e:
            messagebox.showerror("오류", f"회원가입 중 오류 발생:\n{e}")
    
    def show_menu(self):
        if self.main_content: self.main_content.destroy()
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        center = tk.Frame(self.main_content, bg=self.colors['bg'])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(center, text="감정 분석 일기장", font=("맑은 고딕",32,"bold"), bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=(0,10))
        tk.Label(center, text=f"{self.user_id}님의 감정을 기록하고 분석합니다", font=("맑은 고딕",14), bg=self.colors['bg'], fg=self.colors['text_dim']).pack(pady=(0,10))
        
        logout_btn = tk.Button(center, text="로그아웃", font=("맑은 고딕",10), bg=self.colors['panel_bg'], fg=self.colors['text'], 
                              relief=tk.FLAT, padx=15, pady=5, cursor="hand2", command=self.do_logout, bd=0)
        logout_btn.pack(pady=(0,30))
        
        bf = tk.Frame(center, bg=self.colors['bg'])
        bf.pack()
        for text, cmd, bg in [("일기 작성", lambda:self.create_ui('write'), self.colors['accent']),
                               ("주간 감정 통계", lambda:self.create_ui('analysis'), self.colors['button_bg']),
                               ("내가 쓴 일기", lambda:self.create_ui('history'), self.colors['button_bg'])]:
            btn = tk.Button(bf, text=text, font=("맑은 고딕",17,"bold"), bg=bg, fg='white', relief=tk.FLAT, width=22, pady=18, cursor="hand2", command=cmd, activebackground='#2980B9', activeforeground='white', bd=0, highlightthickness=0)
            btn.pack(pady=10)
    
    def do_logout(self):
        """로그아웃 처리"""
        self.user_id = None
        self.current_analysis = None
        messagebox.showinfo("로그아웃", "로그아웃 되었습니다")
        self.show_login()
    
    def create_ui(self, tab='write'):
        if self.main_content: self.main_content.destroy()
        self.status_label = None
        self.main_content = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_content.pack(fill=tk.BOTH, expand=True)

        hdr = tk.Frame(self.main_content, bg=self.colors['accent'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="감정 분석 일기장", font=("맑은 고딕",20,"bold"), bg=self.colors['accent'], fg='white').pack(side=tk.LEFT, padx=25, pady=18)
        back_btn = tk.Button(hdr, text="메인 메뉴", font=("맑은 고딕",12,"bold"), bg=self.colors['accent'], fg='white', relief=tk.FLAT, padx=25, pady=12, cursor="hand2", command=self.show_menu, activebackground='#2980B9', activeforeground='white', bd=0)
        back_btn.pack(side=tk.RIGHT, padx=20)
        
        container = tk.Frame(self.main_content, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)
        
        if tab=='write': self.create_write(container)
        elif tab=='analysis': self.create_analysis(container)
        elif tab=='history': self.create_history(container)
        
        status = tk.Frame(self.main_content, bg=self.colors['panel_bg'], height=30)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(status, text="준비 완료", font=("맑은 고딕",9), bg=self.colors['panel_bg'], fg=self.colors['text_dim'])
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)
        tk.Label(status, text=datetime.now().strftime("%Y년 %m월 %d일"), font=("맑은 고딕",9), bg=self.colors['panel_bg'], fg=self.colors['text_dim']).pack(side=tk.RIGHT, padx=20, pady=8)
    
    def create_write(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        bf = tk.Frame(frame, bg=self.colors['bg'])
        bf.pack(pady=(0,15))
        for text, cmd, bg, icon in [("감정 분석", self.analyze_emotion, self.colors['button_bg'], True),
                               ("작성 완료", self.save_diary, self.colors['accent'], True),
                               ("새로 쓰기", self.clear_inputs, self.colors['panel_bg'], False)]:
            btn = tk.Button(bf, text=text, font=("맑은 고딕",12,"bold"), bg=bg, fg='white' if icon else self.colors['text'],
                     relief=tk.FLAT, width=14, pady=12, cursor="hand2", command=cmd, activebackground='#2980B9' if icon else '#BDC3C7', bd=0, highlightthickness=0)
            btn.pack(side=tk.LEFT, padx=8)
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill=tk.BOTH, expand=True)
        
        inp = tk.Frame(content, bg=self.colors['bg'])
        inp.pack(fill=tk.BOTH, expand=True, pady=(0,12))
        tk.Label(inp, text="오늘의 일기", font=("맑은 고딕",15,"bold"), bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(0,10), anchor=tk.W)
        inf = tk.Frame(inp, bg='white', relief=tk.SOLID, bd=1)
        inf.pack(fill=tk.BOTH, expand=True)
        self.diary_text = scrolledtext.ScrolledText(inf, wrap=tk.WORD, font=("맑은 고딕",11), bg='white', fg='#2C3E50', relief=tk.FLAT, padx=15, pady=15)
        self.diary_text.pack(fill=tk.BOTH, expand=True)
        self.diary_text.insert(1.0, "오늘 하루를 기록해주세요...")
        self.diary_text.bind("<FocusIn>", lambda e: self.diary_text.delete(1.0,tk.END) if self.diary_text.get(1.0,tk.END).strip()=="오늘 하루를 기록해주세요..." else None)

        res = tk.Frame(content, bg=self.colors['bg'])
        res.pack(fill=tk.BOTH, expand=True)
        self.result_title = tk.Label(res, text="분석 결과", font=("맑은 고딕",15,"bold"), bg=self.colors['bg'], fg=self.colors['text'])
        self.result_title.pack(pady=(0,10), anchor=tk.W)
        rf = tk.Frame(res, bg='white', relief=tk.SOLID, bd=1)
        rf.pack(fill=tk.BOTH, expand=True)
        self.result_text = scrolledtext.ScrolledText(rf, wrap=tk.WORD, font=("맑은 고딕",10), bg='white', fg='#34495E', relief=tk.FLAT, padx=15, pady=15, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def create_analysis(self, parent):
        self.analysis_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        self.load_stats()
    
    def create_history(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="내가 쓴 일기", font=("맑은 고딕",16,"bold"), bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(0,15), anchor=tk.W, padx=5)
        
        board = tk.Frame(frame, bg='white', relief=tk.SOLID, bd=1)
        board.pack(fill=tk.BOTH, expand=True, pady=(0,12))

        hdr = tk.Frame(board, bg=self.colors['accent'], height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        for txt, w in [("날짜",18), ("내용",0), ("감정",12)]:
            lbl = tk.Label(hdr, text=txt, font=("맑은 고딕",11,"bold"), bg=self.colors['accent'], fg='white', width=w, anchor=tk.W if txt=="날짜" else tk.CENTER)
            lbl.pack(side=tk.LEFT, fill=tk.X if txt=="내용" else None, expand=txt=="내용", padx=15 if txt!="내용" else 8)

        lf = tk.Frame(board, bg='white')
        lf.pack(fill=tk.BOTH, expand=True)
        self.history_canvas = tk.Canvas(lf, bg='white', highlightthickness=0)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.history_canvas.yview)
        self.history_scrollable = tk.Frame(self.history_canvas, bg='white')
        self.history_scrollable.bind("<Configure>", lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        
        frame_id = self.history_canvas.create_window((0,0), window=self.history_scrollable, anchor="nw")
        
        def _configure_canvas(event):
            self.history_canvas.itemconfig(frame_id, width=event.width)
        self.history_canvas.bind('<Configure>', _configure_canvas)
        
        self.history_canvas.configure(yscrollcommand=sb.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        refresh_btn = tk.Button(frame, text="새로고침", font=("맑은 고딕",12,"bold"), bg=self.colors['button_bg'], fg='white', relief=tk.FLAT, width=16, pady=12, cursor="hand2", command=self.load_history, activebackground='#2980B9', bd=0)
        refresh_btn.pack()
        self.load_history()
    
    def analyze_emotion(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        if not content or content=="오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
            return
        if hasattr(self,'status_label'): self.status_label.config(text="분석 중...")
        threading.Thread(target=self.run_analysis, args=(content,), daemon=True).start()
    
    def run_analysis(self, content):
        try:
            if HAS_ANALYZER:
                result = analyze_diary_with_custom_model(content)
            else:
                import time
                time.sleep(2)
                result = {'primary_emotion':'기쁨','secondary_emotions':['만족','희망'],'emotion_intensity':75,'analysis_score':8,'keywords':['친구','즐거움'],'emotion_tags':['긍정','사교'],'summary':'전반적으로 긍정적인 하루였습니다.'}
            self.root.after(0, self.display_analysis, result)
        except Exception as e:
            self.root.after(0, self.display_error, str(e))
    
    def display_analysis(self, result):
        self.current_analysis = result
        self.result_title.config(text="분석 완료")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        out = ["="*50, "감정 분석 결과", "="*50,
               f"\n주된 감정: {result.get('primary_emotion','N/A')}",
               f"보조 감정: {', '.join(result.get('secondary_emotions',[]))}",
               f"감정 강도: {result.get('emotion_intensity',0)}/100"]
        
        intensity = result.get('emotion_intensity',0)
        bar = "■"*(intensity//5) + "□"*(20-intensity//5)
        out.append(f"[{bar}]")
        out.extend([f"\n분석 점수: {result.get('analysis_score',0)}/10",
                    f"키워드: {', '.join(result.get('keywords',[]))}",
                    f"태그: {', '.join(result.get('emotion_tags',[]))}"])
        if result.get('summary'): out.append(f"\n요약: {result.get('summary')}")
        
        self.result_text.insert(tk.END, "\n".join(out))
        self.result_text.config(state=tk.DISABLED)
        if hasattr(self,'status_label'): self.status_label.config(text="분석 완료")
    
    def display_error(self, error):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"분석 오류\n\n{error}")
        self.result_text.config(state=tk.DISABLED)
        if hasattr(self,'status_label'): self.status_label.config(text="오류 발생")
    
    def save_diary(self):
        content = self.diary_text.get(1.0, tk.END).strip()
        if not content or content=="오늘 하루를 기록해주세요...":
            messagebox.showwarning("알림", "일기를 작성해주세요")
            return
        
        try:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_diary_to_db(self.user_id, date_str, content, self.current_analysis)
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
        if hasattr(self,'result_title'): self.result_title.config(text="분석 결과")
        self.current_analysis = None
        if getattr(self, 'status_label', None): self.status_label.config(text="초기화 완료")
    
    def load_history(self):
        for w in self.history_scrollable.winfo_children(): w.destroy()
        
        try:
            diaries = get_all_diaries(self.user_id)
            
            if not diaries:
                empty = tk.Frame(self.history_scrollable, bg='white')
                empty.pack(fill=tk.BOTH, expand=True)
                empty_label = tk.Label(empty, text="저장된 일기가 없습니다", font=("맑은 고딕",12), bg='white', fg=self.colors['text_dim'])
                empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                for idx, (date, content, emotion) in enumerate(diaries):
                    bg = 'white' if idx%2==0 else self.colors['bg']
                    row = tk.Frame(self.history_scrollable, bg=bg, height=45)
                    row.pack(fill=tk.X)
                    row.pack_propagate(False)
                    date_label = tk.Label(row, text=date.split()[0], font=("맑은 고딕",10), bg=bg, fg=self.colors['text'], width=18, anchor=tk.W)
                    date_label.pack(side=tk.LEFT, padx=15)
                    preview = content[:50]+"..." if len(content)>50 else content
                    content_label = tk.Label(row, text=preview, font=("맑은 고딕",10), bg=bg, fg=self.colors['text'], anchor=tk.W)
                    content_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
                    emotion_label = tk.Label(row, text=emotion if emotion else "-", font=("맑은 고딕",10,"bold"), bg=self.colors['button_bg'] if emotion else bg, fg='white' if emotion else self.colors['text_dim'], width=12)
                    emotion_label.pack(side=tk.LEFT, padx=15)
            
            if getattr(self, 'status_label', None): self.status_label.config(text="목록 로드 완료")
        except Exception as e:
            messagebox.showerror("오류", f"로드 실패:\n{e}")
    
    def load_stats(self):
        try:
            all_diaries, emo_sum = get_diaries_for_stats(self.user_id)
            total = len(all_diaries)
            
            weekly_groups = []
            for i in range(0, len(all_diaries), 7):
                week = all_diaries[i:i+7]
                emotions = {}
                total_int = 0
                for _, date, emo, intensity in week:
                    if emo:
                        emotions[emo] = emotions.get(emo, 0) + 1
                        if intensity:
                            total_int += intensity
                
                if emotions:
                    most = max(emotions.items(), key=lambda x: x[1])[0]
                    avg_int = total_int / len(week) if total_int > 0 else 0
                    weekly_groups.append({
                        'week_num': len(weekly_groups) + 1,
                        'count': len(week),
                        'emotions': emotions,
                        'most_common': most,
                        'avg_intensity': avg_int,
                        'dates': f"{week[-1][1].split()[0]} ~ {week[0][1].split()[0]}"
                    })
            
            sf = tk.Frame(self.analysis_frame, bg='white', relief=tk.SOLID, bd=1)
            sf.pack(fill=tk.BOTH, expand=True)
            
            canvas = tk.Canvas(sf, bg='white', highlightthickness=0)
            sb = ttk.Scrollbar(sf, orient="vertical", command=canvas.yview)
            scrollable = tk.Frame(canvas, bg='white')
            scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            frame_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")
            
            def _configure_canvas(event):
                canvas.itemconfig(frame_id, width=event.width)
            canvas.bind('<Configure>', _configure_canvas)
            
            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            
            if total == 0:
                no_diary_label = tk.Label(scrollable, text="작성된 일기가 없습니다",
                                         font=("맑은 고딕", 12), bg='white', fg=self.colors['text_dim'])
                no_diary_label.pack(expand=True)
            else:
                hdr = tk.Frame(scrollable, bg=self.colors['accent'], height=100)
                hdr.pack(fill=tk.X, padx=0, pady=0)
                hdr.pack_propagate(False)
                
                stats = tk.Frame(hdr, bg=self.colors['accent'])
                stats.pack(expand=True, fill=tk.X, pady=5)
                stats.columnconfigure((0, 1, 2), weight=1)
                
                items = [
                    ("총 일기 수", f"{total}개"),
                    ("분석 주차", f"{len(weekly_groups)}주"),
                    ("주요 감정", emo_sum[0][0] if emo_sum else "-")
                ]
                
                for idx, (lbl, val) in enumerate(items):
                    c = tk.Frame(stats, bg='white', height=90, padx=10, pady=5)
                    c.grid(row=0, column=idx, sticky="nsew", padx=10)
                    c.pack_propagate(False)
                    
                    label_title = tk.Label(c, text=lbl, font=("맑은 고딕", 14),
                                          bg='white', fg=self.colors['text_dim'])
                    label_title.pack(pady=(5, 2))
                    
                    label_value = tk.Label(c, text=val, font=("맑은 고딕", 24, "bold"),
                                          bg='white', fg=self.colors['accent'])
                    label_value.pack()
                
                if weekly_groups:
                    ws = tk.Frame(scrollable, bg='white')
                    ws.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
                    
                    ws_title = tk.Label(ws, text="주간 감정 분석 (7개 단위)",
                                       font=("맑은 고딕", 20, "bold"),
                                       bg='white', fg=self.colors['text'])
                    ws_title.pack(pady=(15, 10), padx=15, anchor=tk.W)
                    
                    for wd in weekly_groups:
                        card = tk.Frame(ws, bg=self.colors['panel_bg'], relief=tk.FLAT, bd=0)
                        card.pack(fill=tk.X, padx=15, pady=5)
                        
                        h = tk.Frame(card, bg=self.colors['accent'], height=60)
                        h.pack(fill=tk.X)
                        h.pack_propagate(False)
                        
                        hc = tk.Frame(h, bg=self.colors['accent'])
                        hc.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)
                        
                        week_label = tk.Label(hc, text=f"Week {wd['week_num']}",
                                             font=("맑은 고딕", 15, "bold"),
                                             bg=self.colors['accent'], fg='white')
                        week_label.pack(side=tk.LEFT)
                        
                        date_label = tk.Label(hc, text=f"{wd['dates']}  |  {wd['count']}개",
                                             font=("맑은 고딕", 12),
                                             bg=self.colors['accent'], fg='white')
                        date_label.pack(side=tk.LEFT, padx=25)
                        
                        main_label = tk.Label(hc, text=f"주요: {wd['most_common']}",
                                             font=("맑은 고딕", 14, "bold"),
                                             bg='white', fg=self.colors['button_bg'],
                                             padx=18, pady=8)
                        main_label.pack(side=tk.RIGHT)
                        
                        chart = tk.Frame(card, bg='white', relief=tk.FLAT, bd=0)
                        chart.pack(fill=tk.X, padx=0, pady=0)
                        
                        max_cnt = max(wd['emotions'].values())
                        
                        for emo, cnt in sorted(wd['emotions'].items(), key=lambda x: x[1], reverse=True):
                            row = tk.Frame(chart, bg='white')
                            row.pack(fill=tk.X, padx=20, pady=8)
                            
                            emo_label = tk.Label(row, text=emo,
                                                font=("맑은 고딕", 15, "bold"),
                                                bg=self.colors['button_bg'], fg='white',
                                                width=9, padx=15, pady=10)
                            emo_label.pack(side=tk.LEFT, padx=(0, 20))
                            
                            cnt_label = tk.Label(row, text=f"{cnt}회",
                                                font=("맑은 고딕", 13),
                                                bg='white', width=6, anchor=tk.W)
                            cnt_label.pack(side=tk.LEFT, padx=(0, 20))
                            
                            bar_bg = tk.Frame(row, bg='#E8E8E8', height=36)
                            bar_bg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
                            
                            bar = tk.Frame(bar_bg, bg=self.colors['accent'], height=36)
                            bar.place(relx=0, rely=0, relwidth=cnt / max_cnt, relheight=1)
                            
                            pct = (cnt / wd['count']) * 100
                            pct_label = tk.Label(row, text=f"{pct:.0f}%",
                                                font=("맑은 고딕", 13, "bold"),
                                                bg='white', fg=self.colors['accent'], width=6)
                            pct_label.pack(side=tk.LEFT)
                        
                        if wd['avg_intensity'] > 0:
                            inf = tk.Frame(card, bg=self.colors['panel_bg'])
                            inf.pack(fill=tk.X, padx=20, pady=(5, 15))
                            
                            intensity_label = tk.Label(inf, text=f"평균 강도: {wd['avg_intensity']:.1f}/100",
                                                      font=("맑은 고딕", 12),
                                                      bg=self.colors['panel_bg'], fg=self.colors['text'])
                            intensity_label.pack(anchor=tk.W, pady=(0, 8))
                            
                            bf = tk.Frame(inf, bg='#E8E8E8', height=20)
                            bf.pack(fill=tk.X)
                            
                            bar = tk.Frame(bf, bg=self.colors['button_bg'], height=20)
                            bar.place(relx=0, rely=0, relwidth=wd['avg_intensity'] / 100, relheight=1)
        
        except Exception as e:
            error_label = tk.Label(self.analysis_frame, text=f"통계 로드 오류:\n{e}",
                                  font=("맑은 고딕", 11), bg=self.colors['bg'], fg='red')
            error_label.pack(expand=True)

def main():
    root = tk.Tk()
    app = MoodTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()