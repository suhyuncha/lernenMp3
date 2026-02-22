import tkinter as tk
from tkinter import filedialog, messagebox
from base_study_view import BaseStudyView
import re
import os

def parse_srt(srt_path):
    # SRT 파싱: [(start, end, text), ...]
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\d+\n|\Z)", re.MULTILINE)
    segments = []
    for match in pattern.finditer(content):
        start = srt_time_to_sec(match.group(2))
        end = srt_time_to_sec(match.group(3))
        text = match.group(4).replace('\n', ' ').strip()
        segments.append({"start": start, "end": end, "text": text})
    return segments

def srt_time_to_sec(s):
    h, m, rest = s.split(":")
    s, ms = rest.split(",")
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

class StudyWithLoadingView(BaseStudyView):
    def __init__(self, parent):
        super().__init__(parent, use_textbox=True)
        self.mp3_path = None
        self.de_srt_path = None
        self.ko_srt_path = None

        # 하단 프레임 생성
        bottom_frame = tk.Frame(self, bg="#f0f0f0")
        bottom_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        # 왼쪽: 버튼 세로 배치
        btn_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        btn_frame.pack(side='left', anchor='n')

        self.mp3_btn = tk.Button(btn_frame, text="MP3 선택", command=self.select_mp3)
        self.mp3_btn.pack(side='top', fill='x', pady=4)
        self.de_srt_btn = tk.Button(btn_frame, text="자막1(독일어) 선택", command=self.select_de_srt)
        self.de_srt_btn.pack(side='top', fill='x', pady=4)
        self.ko_srt_btn = tk.Button(btn_frame, text="자막2(한글) 선택", command=self.select_ko_srt)
        self.ko_srt_btn.pack(side='top', fill='x', pady=4)

        # 오른쪽: 파일명 라벨 세로 배치
        label_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        label_frame.pack(side='left', anchor='n', padx=(20, 0))

        self.mp3_label = tk.Label(label_frame, text="MP3: (미선택)", anchor='w', bg="#f0f0f0")
        self.mp3_label.pack(side='top', fill='x', pady=4)
        self.de_srt_label = tk.Label(label_frame, text="자막1: (미선택)", anchor='w', bg="#f0f0f0")
        self.de_srt_label.pack(side='top', fill='x', pady=4)
        self.ko_srt_label = tk.Label(label_frame, text="자막2: (미선택)", anchor='w', bg="#f0f0f0")
        self.ko_srt_label.pack(side='top', fill='x', pady=4)

    def select_mp3(self):
        path = filedialog.askopenfilename(title="MP3 파일 선택", filetypes=[("MP3 files", "*.mp3")])
        if path:
            self.mp3_path = path
            self.mp3_label.config(text=f"MP3: {path}")
            
            # 파일명에서 확장자 제거 (e.g., "/path/filename.mp3" -> "/path/filename")
            base_path = os.path.splitext(path)[0]
            
            # 독일어 자막 파일 자동 설정 (filename.srt)
            de_srt_path = base_path + ".srt"
            if os.path.exists(de_srt_path):
                self.de_srt_path = de_srt_path
                self.de_srt_label.config(text=f"자막1: {de_srt_path}")
            
            # 한글 자막 파일 자동 설정 (filename_ko.srt)
            ko_srt_path = base_path + "_ko.srt"
            if os.path.exists(ko_srt_path):
                self.ko_srt_path = ko_srt_path
                self.ko_srt_label.config(text=f"자막2: {ko_srt_path}")
            
            self.try_load_all()

    def select_de_srt(self):
        path = filedialog.askopenfilename(title="독일어 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if path:
            self.de_srt_path = path
            self.de_srt_label.config(text=f"자막1: {path}")
            self.try_load_all()

    def select_ko_srt(self):
        path = filedialog.askopenfilename(title="한글 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if path:
            self.ko_srt_path = path
            self.ko_srt_label.config(text=f"자막2: {path}")
            self.try_load_all()

    def try_load_all(self):
        if self.mp3_path and self.de_srt_path and self.ko_srt_path:
            self.load_files(self.mp3_path, self.de_srt_path, self.ko_srt_path)

    def load_files(self, mp3_path, de_srt_path, ko_srt_path):
        de_segments = parse_srt(de_srt_path)
        ko_segments = parse_srt(ko_srt_path)
        # ko_sentences는 ko_segments의 text만 추출
        ko_sentences = [seg["text"] for seg in ko_segments]
        # 독일어 segment와 한글 segment 개수가 다를 수 있으니 맞춰줌
        min_len = min(len(de_segments), len(ko_sentences))
        de_segments = de_segments[:min_len]
        ko_sentences = ko_sentences[:min_len]

        # --- Validity Check ---
        from pydub import AudioSegment
        try:
            audio = AudioSegment.from_file(mp3_path)
            mp3_duration = audio.duration_seconds
        except Exception as e:
            messagebox.showerror("오류", f"MP3 파일을 열 수 없습니다: {e}")
            return
        if not de_segments:
            messagebox.showerror("오류", "SRT 파일에 segment가 없습니다.")
            return
        srt_end = de_segments[-1]["end"]
        # 예: SRT 마지막 end가 mp3 길이보다 2초 이상 크거나, mp3 길이의 80% 미만이면 경고
        if srt_end > mp3_duration + 2 or srt_end < mp3_duration * 0.8:
            messagebox.showwarning(
                "경고",
                f"SRT의 마지막 자막 종료 시각({srt_end:.1f}s)이 MP3 길이({mp3_duration:.1f}s)와 맞지 않습니다.\n"
                "파일을 다시 선택해 주세요."
            )
            return
        self.show_segments(de_segments, mp3_path, ko_sentences)
