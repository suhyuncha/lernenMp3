import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from whisper_worker import whisper_worker, get_audio_duration
from googletrans import Translator
import os
import time
import multiprocessing

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
        self.ko_sentences = []  # 한글 번역 리스트 저장용

        # 프레임 생성
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)

        # 변환 버튼
        self.convert_btn = tk.Button(top_frame, text="변환 시작", command=self.start_conversion, state=tk.DISABLED)
        self.convert_btn.pack(side='left', padx=5)

        # 텍스트 저장 버튼 (초기엔 비활성화)
        self.save_text_btn = tk.Button(top_frame, text="텍스트 저장", command=self.save_raw_text, state=tk.DISABLED)
        self.save_text_btn.pack(side='left', padx=5)

        # # 한글 SRT 저장 버튼 (초기엔 비활성화)
        # self.save_ko_srt_btn = tk.Button(top_frame, text="한글 SRT 저장", command=lambda: self.save_srt_korean(self.last_result), state=tk.DISABLED)
        # self.save_ko_srt_btn.pack(side='left', padx=5)

        # 한글 SRT(전체 번역) 저장 버튼 (초기엔 비활성화)
        self.save_ko_srt_whole_btn = tk.Button(top_frame, text="한글 SRT 저장", command=lambda: self.save_srt_korean_whole(self.last_result), state=tk.DISABLED)
        self.save_ko_srt_whole_btn.pack(side='left', padx=5)

        # 텍스트 디스플레이
        self.text_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=25)
        self.text_box.pack(padx=10, pady=10, expand=True, fill='both')
        self.text_box.insert(tk.END, "파일을 선택하세요.\n")

        # 상태/정보 라벨 (4줄)
        self.status_var = tk.StringVar(value="상태: 변환 실행중이지 않음")
        self.length_var = tk.StringVar(value="오디오 길이: -")
        self.start_var = tk.StringVar(value="시작시간: -")
        self.end_var = tk.StringVar(value="종료시간: -")
        self.elapsed_var = tk.StringVar(value="소요시간: -")

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
                self.start_var.set("시작시간: -")
                self.end_var.set("종료시간: -")
                self.elapsed_var.set("소요시간: -")
            except Exception as e:
                self.length_var.set("오디오 길이: 계산 실패")
                self.start_var.set("시작시간: -")
                self.end_var.set("종료시간: -")
                self.elapsed_var.set("소요시간: -")
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
        self.start_var.set(f"시작시간: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
        self.end_var.set("종료시간: -")
        self.elapsed_var.set("소요시간: -")
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
                self.raw_text = text
                self.last_result = result

                # 변환 시점에서 segment별 번역
                translator = Translator()
                segments = result["segments"]
                self.ko_sentences = []
                for seg in segments:
                    try:
                        ko = translator.translate(seg["text"], src='de', dest='ko').text
                    except Exception:
                        ko = "[번역실패] " + seg["text"]
                    self.ko_sentences.append(ko)
                self.save_srt(result)
                messagebox.showinfo("완료", "변환이 완료되었습니다.\nSRT 파일이 음성파일 위치에 저장되었습니다.")
                self.text_box.delete("1.0", tk.END)
                #if messagebox.askyesno("확인", "변환 결과를 텍스트 박스에 표시할까요?"):
                self.text_box.insert(tk.END, text)
                self.status_var.set("상태: 변환 완료")
                self.length_var.set(f"오디오 길이: {self.audio_duration:.2f}초 ({minutes}분 {seconds}초)")
                self.start_var.set(f"시작시간: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
                self.end_var.set(f"종료시간: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
                self.elapsed_var.set(f"소요시간: {end_time - self.start_time:.2f}초")
                self.save_text_btn.config(state=tk.NORMAL)
                self.save_ko_srt_whole_btn.config(state=tk.NORMAL)

                # StudyView에 데이터 전달
                if hasattr(self.master, "study_view"):
                    self.master.study_view.load_segments(
                        result["segments"],
                        self.mp3_file,
                        self.ko_sentences
                    )
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

    def save_srt_korean_whole(self, result):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        translator = Translator()
        segments = result["segments"]
        ko_sentences = []
        for seg in segments:
            try:
                ko = translator.translate(seg["text"], src='de', dest='ko').text
            except Exception:
                ko = "[번역실패] " + seg["text"]
            ko_sentences.append(ko)

        if self.mp3_file:
            base = os.path.splitext(self.mp3_file)[0]
            srt_path = base + "_ko.srt"
        else:
            srt_path = "output_ko.srt"

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = ko_sentences[i-1]
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        messagebox.showinfo("저장 완료", f"한글 SRT(세그먼트별 번역)가 저장되었습니다:\n{srt_path}")

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
