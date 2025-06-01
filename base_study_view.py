import tkinter as tk
from pydub import AudioSegment
import pygame
import os

class BaseStudyView(tk.Frame):
    def __init__(self, parent, use_textbox=False):
        super().__init__(parent)
        self.segments = []
        self.audio = None
        self.audio_path = None
        self.segment_frames = []  # 각 세그먼트별 Frame 저장
        self.highlighted_set = set()  # 여러 개 하이라이트 지원
        self.use_textbox = use_textbox

        if use_textbox:
            self.text_box = tk.Text(self, height=30, font=("Arial", 11))
            self.text_box.pack(expand=True, fill='both', padx=10, pady=10)
            self.text_box.tag_configure("de", foreground="blue")
            self.text_box.tag_configure("ko", foreground="green")
            self.text_box.bind("<Button-1>", self.on_click)
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
        self.checkbox_vars = []  # 체크박스 상태 저장

        if self.use_textbox:
            self.text_box.delete("1.0", tk.END)
            for i, seg in enumerate(segments):
                de = seg["text"].strip()
                ko = ko_sentences[i].strip() if i < len(ko_sentences) else ""
                self.text_box.insert(tk.END, de + "\n", ("de", f"seg_{i}"))
                self.text_box.insert(tk.END, ko + "\n", ("ko", f"seg_{i}"))
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
        # 체크박스 상태에 따라 하이라이트 토글
        frame, text_frame = self.segment_frames[idx]
        var = self.checkbox_vars[idx]
        if var.get():
            for widget in text_frame.winfo_children():
                widget.configure(bg="#ffffcc")
            text_frame.configure(bg="#ffffcc")
            self.highlighted_set.add(idx)
        else:
            for widget in text_frame.winfo_children():
                widget.configure(bg=self.cget("bg"))
            text_frame.configure(bg=self.cget("bg"))
            self.highlighted_set.discard(idx)

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
        segment = self.audio[int(start_sec * 1000):int(end_sec * 1000)]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            segment.export(tmp_wav.name, format="wav")
            tmp_wav_path = tmp_wav.name
        try:
            pygame.mixer.music.load(tmp_wav_path)
            pygame.mixer.music.play()
        except Exception as e:
            print("오디오 재생 오류:", e)
            return

        def poll_cleanup():
            if pygame.mixer.music.get_busy():
                self.after(100, poll_cleanup)
            else:
                try:
                    os.remove(tmp_wav_path)
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