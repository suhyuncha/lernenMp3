import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import multiprocessing
import time
import os
from whisper_worker import whisper_worker, get_audio_duration
from googletrans import Translator

class ConvertView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.mp3_file = None
        self.model_name = "base"
        self.audio_duration = 0
        self.start_time = 0
        self.process = None
        self.queue = None
        self.raw_text = ""  # 변환된 텍스트 저장용
        self.last_result = None  # 마지막 변환 결과 저장

        # 프레임 생성
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)

        # 변환 버튼
        self.convert_btn = tk.Button(top_frame, text="변환 시작", command=self.start_conversion, state=tk.DISABLED)
        self.convert_btn.pack(side='left', padx=5)

        # 텍스트 저장 버튼 (초기엔 비활성화)
        self.save_text_btn = tk.Button(self, text="텍스트 저장", command=self.save_raw_text, state=tk.DISABLED)
        self.save_text_btn.pack(side='left', padx=5)

        # 한글 SRT 저장 버튼 (초기엔 비활성화)
        self.save_ko_srt_btn = tk.Button(self, text="한글 SRT 저장", command=lambda: self.save_srt_korean(self.last_result), state=tk.DISABLED)
        self.save_ko_srt_btn.pack(side='left', padx=5)

        # 한글 SRT(전체 번역) 저장 버튼 (초기엔 비활성화)
        self.save_ko_srt_whole_btn = tk.Button(self, text="한글 SRT(전체 번역) 저장", command=lambda: self.save_srt_korean_whole(self.last_result), state=tk.DISABLED)
        self.save_ko_srt_whole_btn.pack(side='left', padx=5)

        # 텍스트 디스플레이
        self.text_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=25)
        self.text_box.pack(padx=10, pady=10, expand=True, fill='both')
        self.text_box.insert(tk.END, "파일을 선택하세요.\n")

        # 상태/정보 라벨 (4줄)
        self.status_var = tk.StringVar(value="상태: 변환 실행중이지 않음")
        self.length_var = tk.StringVar(value="오디오 길이: -")
        self.start_var = tk.StringVar(value="시작: -")
        self.end_var = tk.StringVar(value="종료: -")
        self.elapsed_var = tk.StringVar(value="소요: -")

        status_frame = tk.Frame(self)
        status_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(status_frame, textvariable=self.status_var, anchor='w').grid(row=0, column=0, sticky='w')
        tk.Label(status_frame, textvariable=self.length_var, anchor='w').grid(row=1, column=0, sticky='w')
        tk.Label(status_frame, textvariable=self.start_var, anchor='w').grid(row=2, column=0, sticky='w')
        tk.Label(status_frame, textvariable=self.end_var, anchor='w').grid(row=3, column=0, sticky='w')
        tk.Label(status_frame, textvariable=self.elapsed_var, anchor='w').grid(row=4, column=0, sticky='w')

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="MP3 파일 선택",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.mp3_file = file_path
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert(tk.END, f"선택된 파일: {os.path.basename(file_path)}\n")
            self.convert_btn.config(state=tk.NORMAL)
            self.status_var.set("상태: 변환 실행중이지 않음")
            try:
                duration = get_audio_duration(file_path)
                self.audio_duration = duration
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.length_var.set(f"오디오 길이: {duration:.2f}초 ({minutes}분 {seconds}초)")
                self.start_var.set("시작: -")
                self.end_var.set("종료: -")
                self.elapsed_var.set("소요: -")
            except Exception as e:
                self.length_var.set("오디오 길이: 계산 실패")
                self.start_var.set("시작: -")
                self.end_var.set("종료: -")
                self.elapsed_var.set("소요: -")
                self.text_box.insert(tk.END, f"오디오 길이 계산 오류: {e}\n")

    def start_conversion(self):
        if not self.mp3_file:
            messagebox.showerror("오류", "MP3 파일을 먼저 선택하세요.")
            return
        self.convert_btn.config(state=tk.DISABLED)
        self.status_var.set("상태: 변환중...")
        self.text_box.insert(tk.END, "변환을 시작합니다...\n")
        minutes = int(self.audio_duration // 60)
        seconds = int(self.audio_duration % 60)
        self.start_time = time.time()
        self.length_var.set(f"오디오 길이: {self.audio_duration:.2f}초 ({minutes}분 {seconds}초)")
        self.start_var.set(f"시작: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
        self.end_var.set("종료: -")
        self.elapsed_var.set("소요: -")
        # 프로세스와 큐 생성
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=whisper_worker,
            args=(self.mp3_file, self.model_name, self.queue)
        )
        self.process.start()
        self.after(500, self.check_process)  # self.parent.after → self.after

    def check_process(self):
        if self.queue is not None and not self.queue.empty():
            data = self.queue.get()
            end_time = time.time()
            minutes = int(self.audio_duration // 60)
            seconds = int(self.audio_duration % 60)
            if data["error"]:
                self.status_var.set("상태: 오류 발생")
                messagebox.showerror("오류", data["error"])
            else:
                result = data["result"]
                text = result["text"]
                self.raw_text = text  # 변환된 텍스트 저장
                self.last_result = result  # 마지막 변환 결과 저장
                self.save_srt(result)
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, text)
                self.status_var.set("상태: 변환 완료")
                self.length_var.set(f"오디오 길이: {self.audio_duration:.2f}초 ({minutes}분 {seconds}초)")
                self.start_var.set(f"시작: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
                self.end_var.set(f"종료: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
                self.elapsed_var.set(f"소요: {end_time - self.start_time:.2f}초")
                messagebox.showinfo("완료", "변환이 완료되었습니다.\nSRT 파일이 음성파일 위치에 저장되었습니다.")
                self.save_text_btn.config(state=tk.NORMAL)  # 텍스트 저장 버튼 활성화
                self.save_ko_srt_btn.config(state=tk.NORMAL)  # 한글 SRT 저장 버튼 활성화
                self.save_ko_srt_whole_btn.config(state=tk.NORMAL)  # 한글 SRT(전체 번역) 저장 버튼 활성화
            self.convert_btn.config(state=tk.NORMAL)
            self.process = None
            self.queue = None
        elif self.process is not None and self.process.is_alive():
            self.after(500, self.check_process)
        else:
            # 예외적으로 프로세스가 종료됐지만 큐가 비어있으면 에러 처리
            self.status_var.set("상태: 오류 발생")
            messagebox.showerror("오류", "예상치 못한 오류가 발생했습니다.")
            self.convert_btn.config(state=tk.NORMAL)
            self.process = None
            self.queue = None

    def save_srt(self, result):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        # mp3 파일과 같은 폴더에 저장
        if self.mp3_file:
            base = os.path.splitext(self.mp3_file)[0]
            srt_path = base + ".srt"
        else:
            srt_path = "output.srt"

        # 기본 SRT 저장
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"], start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    def save_srt_korean(self, result):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        translator = Translator()
        if self.mp3_file:
            base = os.path.splitext(self.mp3_file)[0]
            srt_path = base + "_ko.srt"
        else:
            srt_path = "output_ko.srt"

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"], start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                # 독일어 → 한글 번역
                try:
                    translated = translator.translate(text, src='de', dest='ko').text
                except Exception as e:
                    translated = "[번역실패] " + text
                f.write(f"{i}\n{start} --> {end}\n{translated}\n\n")
        messagebox.showinfo("저장 완료", f"한글 SRT가 저장되었습니다:\n{srt_path}")

    def save_srt_korean_whole(self, result):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        translator = Translator()
        if self.mp3_file:
            base = os.path.splitext(self.mp3_file)[0]
            srt_path = base + "_ko_whole.srt"
        else:
            srt_path = "output_ko_whole.srt"

        # 1. 전체 텍스트 번역
        full_text = result["text"].strip()
        try:
            translated_full = translator.translate(full_text, src='de', dest='ko').text
        except Exception as e:
            messagebox.showerror("번역 오류", str(e))
            return

        # 2. 문장 단위로 나누기 (예시: 마침표 기준)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', translated_full)
        segments = result["segments"]
        n = len(segments)

        # 3. segment 개수에 맞게 문장 분배 (간단하게: 부족하면 빈 문자열, 넘치면 합침)
        # 더 정교하게 하려면 문장 길이/segment 길이 비율로 분배 가능
        if len(sentences) < n:
            sentences += [''] * (n - len(sentences))
        elif len(sentences) > n:
            # 문장이 더 많으면, 마지막 segment에 모두 합침
            sentences = sentences[:n-1] + [' '.join(sentences[n-1:])]

        # 4. SRT 저장
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = sentences[i-1].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        messagebox.showinfo("저장 완료", f"한글 SRT(전체 번역)가 저장되었습니다:\n{srt_path}")

    def save_raw_text(self):
        if not self.raw_text:
            messagebox.showerror("오류", "저장할 텍스트가 없습니다.")
            return
        file_path = filedialog.asksaveasfilename(
            title="텍스트 파일로 저장",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.raw_text)
            messagebox.showinfo("저장 완료", f"텍스트가 저장되었습니다:\n{file_path}")

class StudyView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # 공부하기 뷰의 위젯/로직 구현
        tk.Label(self, text="공부하기 뷰입니다.", font=("Arial", 18)).pack(pady=30)
        # 원하는 기능 추가

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP3 → 텍스트 변환기")
        self.geometry("900x600")

        notebook = ttk.Notebook(self)
        self.convert_view = ConvertView(notebook)
        self.study_view = StudyView(notebook)

        notebook.add(self.convert_view, text="변환하기")
        notebook.add(self.study_view, text="공부하기")
        notebook.pack(expand=True, fill='both')

        # 메뉴 예시 (공통 메뉴)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="MP3 파일 열기", command=self.convert_view.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="종료", command=self.quit)
        menubar.add_cascade(label="파일", menu=filemenu)
        self.config(menu=menubar)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
