import tkinter as tk
from pydub import AudioSegment
import pygame
import os
from tkinter import filedialog
import subprocess

class BaseStudyView(tk.Frame):
    def __init__(self, parent, use_textbox=False):
        super().__init__(parent)
        self.segments = []
        self.audio = None
        self.audio_path = None
        self.segment_frames = []  # 각 세그먼트별 Frame 저장
        self.highlighted_set = set()  # 여러 개 하이라이트 지원
        self.ko_visibility = {}  # 각 segment의 한글 자막 표시 여부 {idx: True/False}
        self.use_textbox = use_textbox

        if use_textbox:
            # 상단 옵션 프레임
            options_container = tk.Frame(self, bg="#f0f0f0")
            options_container.pack(pady=5, padx=10, fill='x')
            
            # 1. 재생 속도 옵션
            speed_frame = tk.Frame(options_container, bg="#f0f0f0")
            speed_frame.pack(side='top', fill='x', pady=2)
            
            tk.Label(speed_frame, text="재생 속도:", bg="#f0f0f0", font=("Arial", 10)).pack(side='left', padx=(0, 10))
            
            self.speed_var = tk.DoubleVar(value=1.0)
            speed_options = [0.5, 0.8, 1.0]
            
            for speed in speed_options:
                tk.Radiobutton(
                    speed_frame,
                    text=f"{speed}배",
                    variable=self.speed_var,
                    value=speed,
                    bg="#f0f0f0",
                    font=("Arial", 10)
                ).pack(side='left', padx=5)
            
            # 2. 한글 자막 전체 표시/숨김 옵션
            ko_all_frame = tk.Frame(options_container, bg="#f0f0f0")
            ko_all_frame.pack(side='top', fill='x', pady=2)
            
            self.ko_all_visible_var = tk.BooleanVar(value=True)
            tk.Checkbutton(
                ko_all_frame,
                text="한글 자막 전체 표시",
                variable=self.ko_all_visible_var,
                command=self.toggle_all_ko_visibility,
                bg="#f0f0f0",
                font=("Arial", 10)
            ).pack(side='left', padx=(0, 10))
            
            # 텍스트박스
            self.text_box = tk.Text(self, height=30, font=("Arial", 11))
            self.text_box.pack(expand=True, fill='both', padx=10, pady=10)
            self.text_box.tag_configure("de", foreground="blue")
            self.text_box.tag_configure("ko", foreground="green")
            self.text_box.bind("<Button-1>", self.on_click)
            self.text_box.bind("<Button-3>", self.show_context_menu)  # 오른쪽 클릭
            self.text_box.bind("<Control-Button-1>", self.show_context_menu)  # Mac 터치패드 두 손가락 클릭 지원
            self.highlight_btns = []
            # 컨텍스트 메뉴 생성
            self.context_menu = tk.Menu(self, tearoff=0)
            self.context_menu.add_command(label="복사", command=self.copy_selected_text)
        else:
            canvas = tk.Canvas(self)
            scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            self.inner_frame = tk.Frame(canvas)
            self.inner_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        pygame.mixer.init()

    def show_segments(self, segments, audio_path, ko_sentences):
        self.segments = segments
        self.audio_path = audio_path
        self.audio = AudioSegment.from_file(audio_path)
        self.highlighted_set = set()
        #self.checkbox_vars = []  # 체크박스 상태 저장

        if self.use_textbox:
            # 기존 버튼 제거
            for btn in getattr(self, "highlight_btns", []):
                btn.destroy()
            for btn in getattr(self, "ko_checkbox_btns", []):
                btn.destroy()
            self.highlight_btns = []
            self.ko_checkbox_btns = []
            self.ko_visibility = {}  # 초기화
            self.text_box.delete("1.0", tk.END)
            for i, seg in enumerate(segments):
                de = seg["text"].strip()
                ko = ko_sentences[i].strip() if i < len(ko_sentences) else ""
                
                # 별(★) 버튼 - 하이라이트 토글
                btn_highlight = tk.Button(
                    self.text_box,
                    text="★",
                    width=1,
                    relief="flat",
                    command=lambda idx=i: self.toggle_highlight(idx)
                )
                self.highlight_btns.append(btn_highlight)
                self.text_box.window_create(tk.END, window=btn_highlight)
                
                # 체크박스 버튼 - 한글 자막 표시/숨김 토글 (초기값: 표시됨)
                ko_visible = True
                self.ko_visibility[i] = ko_visible
                checkbox_text = "☑"  # 체크됨
                checkbox_btn = tk.Button(
                    self.text_box,
                    text=checkbox_text,
                    width=1,
                    relief="flat",
                    command=lambda idx=i: self.toggle_ko_visibility(idx),
                    font=("Arial", 9)
                )
                self.ko_checkbox_btns.append(checkbox_btn)
                self.text_box.window_create(tk.END, window=checkbox_btn)
                
                # 독일어 텍스트 삽입
                self.text_box.insert(tk.END, " " + de + "\n", ("de", f"seg_{i}"))
                
                # 한글 텍스트 삽입 (초기에는 보임)
                indent = " " * (3)
                self.text_box.insert(tk.END, indent + ko + "\n", ("ko", f"ko_seg_{i}"))
                
                # 세그먼트 간 공백 줄
                self.text_box.insert(tk.END, "\n")

        else:
            # 기존 프레임 삭제
            for f in getattr(self, "segment_frames", []):
                f.destroy()
            self.segment_frames = []
            self.checkbox_vars = []
            for i, seg in enumerate(segments):
                de = seg["text"].strip()
                ko = ko_sentences[i].strip() if i < len(ko_sentences) else ""
                frame = tk.Frame(self.inner_frame, pady=2)
                frame.pack(fill="x", padx=5, pady=2)
                # 체크박스 (왼쪽)
                var = tk.IntVar()
                chk = tk.Checkbutton(
                    frame,
                    variable=var,
                    command=lambda idx=i: self.toggle_highlight(idx),
                    width=2
                )
                chk.grid(row=0, column=0, rowspan=2, padx=(0, 6), sticky="n")
                self.checkbox_vars.append(var)
                # 텍스트 부분(오른쪽)만 별도 Frame으로 감싸서 하이라이트 적용
                text_frame = tk.Frame(frame)
                text_frame.grid(row=0, column=1, rowspan=2, sticky="w")

                # --- 독일어 한 줄 ---
                de_line = tk.Frame(text_frame)
                de_line.pack(anchor="w")
                def add_word_labels(parent, text, fg):
                    words = text.split()
                    for word in words:
                        lbl = tk.Label(parent, text=word + " ", fg=fg, font=("Arial", 11))
                        lbl.pack(side="left", anchor="w")
                add_word_labels(de_line, de, "blue")
                # 줄 전체에 클릭 이벤트 바인딩
                de_line.bind("<Button-1>", lambda e, idx=i: self.play_segment_by_idx(idx))

                # --- 한글 한 줄 ---
                ko_line = tk.Frame(text_frame)
                ko_line.pack(anchor="w")
                add_word_labels(ko_line, ko, "green")
                ko_line.bind("<Button-1>", lambda e, idx=i: self.play_segment_by_idx(idx))

                self.segment_frames.append((frame, text_frame))
        
    def on_click(self, event):
        index = self.text_box.index(f"@{event.x},{event.y}")
        tags = self.text_box.tag_names(index)
        seg_idx = None
        for tag in tags:
            if tag.startswith("seg_"):
                seg_idx = int(tag.split("_")[1])
                break
        if seg_idx is not None and 0 <= seg_idx < len(self.segments):
            seg = self.segments[seg_idx]
            print(f"재생할 세그먼트: {seg_idx + 1}, 시작: {seg['start']}, 종료: {seg['end']}")
            self.play_segment(seg["start"], seg["end"])
        # 빈 줄(태그 없음) 클릭 시 아무 동작 안 함

    def toggle_highlight(self, idx):
        seg_tag = f"seg_{idx}"
        # 하이라이트 토글
        current_bg = self.text_box.tag_cget(seg_tag, "background")
        if current_bg == "" or current_bg == "SystemWindow":
            self.text_box.tag_configure(seg_tag, background="#ffffcc")
            self.highlighted_set.add(idx)
        else:
            self.text_box.tag_configure(seg_tag, background="")
            self.highlighted_set.discard(idx)

    def toggle_ko_visibility(self, idx):
        """문장 단위로 한글 자막 표시/숨김 토글"""
        ko_tag = f"ko_seg_{idx}"
        
        # 현재 상태 토글
        self.ko_visibility[idx] = not self.ko_visibility[idx]
        
        if self.ko_visibility[idx]:
            # 한글 자막 보이기 (녹색)
            self.text_box.tag_configure(ko_tag, foreground="green")
            # 체크박스 버튼 표시 (☑)
            if idx < len(self.ko_checkbox_btns):
                self.ko_checkbox_btns[idx].config(text="☑")
        else:
            # 한글 자막 숨기기 (흰색 = 배경색과 같음)
            self.text_box.tag_configure(ko_tag, foreground="white")
            # 체크박스 버튼 표시 (☐)
            if idx < len(self.ko_checkbox_btns):
                self.ko_checkbox_btns[idx].config(text="☐")

    def toggle_all_ko_visibility(self):
        """모든 문장의 한글 자막을 일괄 표시/숨김"""
        # 전체 체크박스 상태 확인
        show_all = self.ko_all_visible_var.get()
        
        # 모든 문장에 대해 일괄 처리
        for idx in range(len(self.segments)):
            ko_tag = f"ko_seg_{idx}"
            
            if show_all:
                # 한글 자막 모두 보이기 (녹색)
                self.text_box.tag_configure(ko_tag, foreground="green")
                self.ko_visibility[idx] = True
                # 체크박스 버튼 표시 (☑)
                if idx < len(self.ko_checkbox_btns):
                    self.ko_checkbox_btns[idx].config(text="☑")
            else:
                # 한글 자막 모두 숨기기 (흰색)
                self.text_box.tag_configure(ko_tag, foreground="white")
                self.ko_visibility[idx] = False
                # 체크박스 버튼 표시 (☐)
                if idx < len(self.ko_checkbox_btns):
                    self.ko_checkbox_btns[idx].config(text="☐")

    def play_segment_by_idx(self, idx):
        seg = self.segments[idx]
        print(f"Playing segment {idx}: {seg['start']} - {seg['end']}") # 디버깅용 출력
        self.play_segment(seg["start"], seg["end"])

    def play_segment(self, start_sec, end_sec):
        if not self.audio or not self.audio_path:
            print("No audio loaded")
            return
        if end_sec - start_sec < 0.5:
            end_sec = start_sec + 0.5
        import tempfile
        import time
        import subprocess
        
        segment = self.audio[int(start_sec * 1000):int(end_sec * 1000)]
        
        # 선택된 재생 속도 가져오기
        speed = getattr(self, 'speed_var', None)
        playback_speed = speed.get() if speed else 1.0
        
        # 임시 WAV 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            tmp_wav_path = tmp_wav.name
        
        # 원본 segment를 WAV로 저장
        segment.export(tmp_wav_path, format="wav")
        
        # 속도 변환이 필요하면 ffmpeg 사용
        cleanup_paths = [tmp_wav_path]
        play_path = tmp_wav_path
        
        if playback_speed != 1.0:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_out:
                tmp_wav_out_path = tmp_wav_out.name
            cleanup_paths.append(tmp_wav_out_path)
            
            try:
                # ffmpeg으로 속도 변환
                cmd = [
                    'ffmpeg',
                    '-i', tmp_wav_path,
                    '-filter:a', f'atempo={playback_speed}',
                    '-y',
                    tmp_wav_out_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    play_path = tmp_wav_out_path
                else:
                    print(f"속도 변환 실패, 원본으로 재생합니다")
            except Exception as e:
                print(f"속도 변환 오류: {e}")
        
        # 오디오 재생
        try:
            pygame.mixer.music.load(play_path)
            pygame.mixer.music.play()
        except Exception as e:
            print("오디오 재생 오류:", e)
            for path in cleanup_paths:
                try:
                    os.remove(path)
                except:
                    pass
            return

        # 재생 완료 후 정리
        def poll_cleanup():
            if pygame.mixer.music.get_busy():
                self.after(100, poll_cleanup)
            else:
                for path in cleanup_paths:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        
        poll_cleanup()

    def show_copy_tooltip(self, event, word, label):
        # 이미 떠있는 copy 버튼이 있으면 제거
        self.hide_copy_tooltip()
        x = label.winfo_rootx() - self.winfo_rootx() + label.winfo_width() // 2
        y = label.winfo_rooty() - self.winfo_rooty() + label.winfo_height()
        self.copy_btn = tk.Button(self, text="copy", font=("Arial", 8), relief="solid",
                                  command=lambda w=word: self.copy_word(w))
        self.copy_btn.place(x=x, y=y)

    def hide_copy_tooltip(self):
        if hasattr(self, "copy_btn") and self.copy_btn:
            self.copy_btn.destroy()
            self.copy_btn = None

    def copy_word(self, word):
        self.clipboard_clear()
        self.clipboard_append(word)
        self.hide_copy_tooltip()

    def load_files(self):
        mp3_path = filedialog.askopenfilename(title="MP3 파일 선택", filetypes=[("MP3 files", "*.mp3")])
        if not mp3_path:
            return
        self.after(100, lambda: self.ask_de_srt(mp3_path))

    def ask_de_srt(self, mp3_path):
        de_srt_path = filedialog.askopenfilename(title="독일어 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if not de_srt_path:
            return
        self.after(100, lambda: self.ask_ko_srt(mp3_path, de_srt_path))

    def ask_ko_srt(self, mp3_path, de_srt_path):
        ko_srt_path = filedialog.askopenfilename(title="한글 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if not ko_srt_path:
            return
        # ...이후 기존 로직...

    def show_context_menu(self, event):
        try:
            if self.text_box.tag_ranges(tk.SEL):
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selected_text(self):
        try:
            selected = self.text_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected)
        except tk.TclError:
            pass