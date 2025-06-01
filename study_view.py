import tkinter as tk
from pydub import AudioSegment
import pygame
import os


class StudyView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.segments = []
        self.audio = None
        self.audio_path = None

        self.text_box = tk.Text(self, height=30, font=("Arial", 12))
        self.text_box.pack(expand=True, fill='both', padx=10, pady=10)
        self.text_box.tag_configure("de", foreground="blue")
        self.text_box.tag_configure("ko", foreground="green")

        self.text_box.bind("<Button-1>", self.on_click)

        pygame.mixer.init()

    def load_segments(self, segments, audio_path, ko_sentences):
        """segments: Whisper segments, audio_path: mp3, ko_sentences: 한글 번역 리스트"""
        self.segments = segments
        self.audio_path = audio_path
        self.audio = AudioSegment.from_file(audio_path)
        self.text_box.delete("1.0", tk.END)
        for i, seg in enumerate(segments):
            de = seg["text"].strip()
            ko = ko_sentences[i].strip() if i < len(ko_sentences) else ""
            # 독일어 줄
            start_idx = self.text_box.index(tk.END)
            self.text_box.insert(tk.END, de + "\n", ("de", f"seg_{i}"))
            # 한글 줄
            self.text_box.insert(tk.END, ko + "\n", ("ko", f"seg_{i}"))
            # 빈 줄(구분용, 태그 없음)
            self.text_box.insert(tk.END, "\n")

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

    def play_segment(self, start_sec, end_sec):
        if not self.audio or not self.audio_path:
            return
        # 최소 길이 0.5초로 강제
        if end_sec - start_sec < 0.5:
            end_sec = start_sec + 0.5
        import tempfile
        segment = self.audio[int(start_sec * 1000):int(end_sec * 1000)]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            segment.export(tmp_wav.name, format="wav")
            tmp_wav_path = tmp_wav.name
        # pygame으로 wav 재생
        pygame.mixer.music.load(tmp_wav_path)
        pygame.mixer.music.play()

        # polling 방식으로 재생이 끝나면 파일 삭제
        def poll_cleanup():
            if pygame.mixer.music.get_busy():
                self.after(100, poll_cleanup)
            else:
                try:
                    os.remove(tmp_wav_path)
                except Exception:
                    pass
        poll_cleanup()
