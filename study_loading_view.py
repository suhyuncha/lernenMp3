import tkinter as tk
from tkinter import filedialog, messagebox
from base_study_view import BaseStudyView
import re

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
        # 상단에 별도 프레임 생성 (텍스트박스보다 먼저 pack!)
        top_frame = tk.Frame(self, height=36, bg="#f0f0f0")
        top_frame.pack(side='bottom', fill='x')  # 하단에 배치
        self.mp3_btn = tk.Button(top_frame, text="MP3 선택", command=self.select_mp3)
        self.mp3_btn.pack(side='left', padx=10, pady=6)
        self.de_srt_btn = tk.Button(top_frame, text="자막1(독일어) 선택", command=self.select_de_srt)
        self.de_srt_btn.pack(side='left', padx=10, pady=6)
        self.ko_srt_btn = tk.Button(top_frame, text="자막2(한글) 선택", command=self.select_ko_srt)
        self.ko_srt_btn.pack(side='left', padx=10, pady=6)
        # 텍스트박스는 BaseStudyView에서 이미 pack됨 (여기서 pack하지 않음)

    def select_mp3(self):
        path = filedialog.askopenfilename(title="MP3 파일 선택", filetypes=[("MP3 files", "*.mp3")])
        if path:
            self.mp3_path = path
            self.mp3_btn.config(text=f"MP3: {path.split('/')[-1]}")
            self.try_load_all()

    def select_de_srt(self):
        path = filedialog.askopenfilename(title="독일어 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if path:
            self.de_srt_path = path
            self.de_srt_btn.config(text=f"자막1: {path.split('/')[-1]}")
            self.try_load_all()

    def select_ko_srt(self):
        path = filedialog.askopenfilename(title="한글 SRT 선택", filetypes=[("SRT files", "*.srt")])
        if path:
            self.ko_srt_path = path
            self.ko_srt_btn.config(text=f"자막2: {path.split('/')[-1]}")
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
