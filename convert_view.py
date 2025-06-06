import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from whisper_worker import whisper_worker, get_audio_duration
from googletrans import Translator
import os
import time
import multiprocessing
import re
from study_loading_view import parse_srt

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

        # --- 번역기 선택 라디오버튼 추가 ---
        self.translator_var = tk.StringVar(value="google")
        radio_frame = tk.Frame(self)
        radio_frame.pack(pady=5)
        tk.Label(radio_frame, text="번역기 선택:").pack(side='left')
        tk.Radiobutton(radio_frame, text="Google", variable=self.translator_var, value="google").pack(side='left')
        tk.Radiobutton(radio_frame, text="Papago", variable=self.translator_var, value="papago").pack(side='left')
        # 필요시 다른 번역기도 추가

        # 프레임 생성
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)

        # 변환 버튼
        self.convert_btn = tk.Button(top_frame, text="변환 시작", command=self.start_conversion, state=tk.DISABLED)
        self.convert_btn.pack(side='left', padx=5)

        # 텍스트 저장 버튼 (초기엔 비활성화)
        self.save_text_btn = tk.Button(top_frame, text="텍스트 저장", command=self.save_raw_text, state=tk.DISABLED)
        self.save_text_btn.pack(side='left', padx=5)

        # 상단: 실행 경과용 info_text_box (스크롤 지원)
        self.info_text_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=5, font=("Arial", 10), bg="#f0f0f0")
        self.info_text_box.pack(padx=10, pady=(10, 2), fill='x')
        self.info_text_box.config(state=tk.DISABLED)

        # 하단: 추출 결과용 text_box
        self.text_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=25)
        self.text_box.pack(padx=10, pady=(2, 10), expand=True, fill='both')

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

    def log_info(self, msg):
        self.info_text_box.config(state=tk.NORMAL)
        self.info_text_box.insert(tk.END, msg + "\n")
        self.info_text_box.see(tk.END)
        self.info_text_box.config(state=tk.DISABLED)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="MP3 파일 선택",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.mp3_file = file_path
            self.log_info(f"선택된 파일: {file_path}")
            self.text_box.delete("1.0", tk.END)
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
        self.log_info("변환을 시작합니다...")
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

    def get_translator(self):
        if self.translator_var.get() == "google":
            return Translator()
        elif self.translator_var.get() == "papago":
            # return Papago(client_id=..., client_secret=...)
            # 실제 Papago 연동 코드 필요
            pass
        else:
            return Translator()  # 기본값

    def check_process(self):
        if self.queue is not None and not self.queue.empty():
            data = self.queue.get()
            end_time = time.time()
            minutes = int(self.audio_duration // 60)
            seconds = int(self.audio_duration % 60)
            if data["error"]:
                self.status_var.set("상태: 오류 발생")
                self.log_info(f"[오류] {data['error']}")
                messagebox.showerror("오류", data["error"])
            else:
                result = data["result"]
                text = result["text"]
                self.raw_text = text
                self.last_result = result

                # 1. 구두점 기준 문장 단위로 변환
                segments = split_segments_by_period(result["segments"])

                # 추출 완료 메시지 info_text_box에 출력
                self.log_info("추출이 완료되었습니다.\n번역을 시작합니다..")

                # 화면을 강제로 refresh
                self.update_idletasks()

                # --- 선택된 번역기 사용 ---
                self.ko_sentences = []
                translator = self.get_translator()
                for seg in segments:
                    try:
                        if self.translator_var.get() == "google":
                            ko = translator.translate(seg["text"], src='de', dest='ko').text
                        elif self.translator_var.get() == "papago":
                            ko = "[파파고 미구현]"  # 실제 Papago 연동 필요
                        else:
                            ko = "[번역기 미지정] " + seg["text"]
                    except Exception:
                        ko = "[번역실패] " + seg["text"]
                    self.ko_sentences.append(ko)

                # 3. SRT 저장(독일어/한글) 모두 문장 단위 segments 기준, 싱크 동일하게
                if self.mp3_file:
                    base = os.path.splitext(self.mp3_file)[0]
                    de_srt_path = base + ".srt"
                    ko_srt_path = base + "_ko.srt"
                else:
                    de_srt_path = "output.srt"
                    ko_srt_path = "output_ko.srt"
                self.save_srt_by_sentences(segments, de_srt_path)
                self.save_srt_korean_by_sentences(segments, self.ko_sentences, ko_srt_path)

                # SRT 저장 후 StudyView에 데이터 전달
                if hasattr(self.master, "study_view"):
                    de_segments = parse_srt(de_srt_path)
                    ko_segments = parse_srt(ko_srt_path)
                    ko_texts = [seg["text"] for seg in ko_segments]
                    self.master.study_view.load_segments(
                        de_segments,
                        self.mp3_file,
                        ko_texts
                    )

                messagebox.showinfo("완료", f"변환이 완료되었습니다.\nSRT 파일이 음성파일 위치에 저장되었습니다.\n\n- 독일어 SRT 및 한글 SRT")
                # 최종 추출 결과만 하단 text_box에 출력
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, text)
                self.status_var.set("상태: 변환 완료")
                self.length_var.set(f"오디오 길이: {self.audio_duration:.2f}초 ({minutes}분 {seconds}초)")
                self.start_var.set(f"시작시간: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
                self.end_var.set(f"종료시간: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
                self.elapsed_var.set(f"소요시간: {end_time - self.start_time:.2f}초")
                self.save_text_btn.config(state=tk.NORMAL)
                # self.save_ko_srt_whole_btn.config(state=tk.NORMAL)  # 한글 SRT 저장 버튼 활성화 제거

                # StudyView에 데이터 전달
                if hasattr(self.master, "study_view"):
                    self.master.study_view.load_segments(
                        segments,  # 변환된 segments 사용
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

    def save_srt_by_sentences(self, segments, srt_path):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    def save_srt_korean_by_sentences(self, segments, ko_sentences, srt_path):
        def format_timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = ko_sentences[i-1] if i-1 < len(ko_sentences) else ""
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

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

    def save_srt(self, result):
        # 더 이상 사용하지 않음 (문장 단위 SRT만 저장)
        pass

    def save_srt_korean_whole(self, result):
        # 더 이상 사용하지 않음 (문장 단위 SRT만 저장)
        pass

def split_segments_by_period(segments):
    import re
    # 1. 모든 세그먼트 텍스트를 순서대로 이어붙임
    texts = [seg["text"].strip() for seg in segments]
    full_text = " ".join(texts)
    # 2. 문장 단위로 쪼개기 (오직 . ! ? 만 기준)
    # 쉼표(,)는 분할 기준에서 제외
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_text) if s.strip()]
    # 3. 문장별로 원본 세그먼트의 시간정보를 추적
    new_segments = []
    acc_len = 0
    seg_idx = 0
    char_idx = 0
    for sentence in sentences:
        # 문장이 전체 텍스트에서 어디서 시작하는지 찾기
        sent_start = full_text.find(sentence, char_idx)
        sent_end = sent_start + len(sentence)
        # 해당 문장이 포함된 세그먼트 범위 찾기
        seg_start_idx = None
        seg_end_idx = None
        seg_char_start = 0
        for i, seg in enumerate(segments):
            seg_text = seg["text"].strip()
            seg_len = len(seg_text)
            seg_char_end = seg_char_start + seg_len
            # 문장 시작이 이 세그먼트에 포함?
            if seg_start_idx is None and seg_char_end > sent_start:
                seg_start_idx = i
            # 문장 끝이 이 세그먼트에 포함?
            if seg_char_end >= sent_end:
                seg_end_idx = i
                break
            seg_char_start = seg_char_end + 1  # +1 for the space added above
        # 시작/끝 시간 할당
        if seg_start_idx is not None and seg_end_idx is not None:
            start = segments[seg_start_idx]["start"]
            end = segments[seg_end_idx]["end"]
            new_segments.append({
                "start": start,
                "end": end,
                "text": sentence
            })
        char_idx = sent_end
    return new_segments

def merge_segments_to_sentences(segments):
    import re
    merged = []
    buffer = ""
    start_time = None
    for seg in segments:
        if start_time is None:
            start_time = seg["start"]
        buffer += (" " if buffer else "") + seg["text"].strip()
        if re.search(r'[.!?]["\']?$', buffer.strip()):
            merged.append({
                "start": start_time,
                "end": seg["end"],
                "text": buffer.strip()
            })
            buffer = ""
            start_time = None
    # 남은 buffer 처리
    if buffer:
        merged.append({
            "start": start_time if start_time is not None else segments[-1]["start"],
            "end": segments[-1]["end"],
            "text": buffer.strip()
        })
    return merged
