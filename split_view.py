import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading
import multiprocessing
import subprocess
from whisper_worker import whisper_worker

class SplitView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.mp3_file = None
        self.output_dir = None
        self.is_processing = False
        self.queue = None
        self.process = None
        
        # 상단: 파일 선택 버튼
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=10, padx=10, fill='x')
        
        self.select_btn = tk.Button(
            button_frame,
            text="MP3 파일 선택",
            command=self.select_mp3_file,
            font=("Arial", 10)
        )
        self.select_btn.pack(side='left', padx=5)
        
        self.split_btn = tk.Button(
            button_frame,
            text="파일 분리 시작",
            command=self.start_split,
            state=tk.DISABLED,
            font=("Arial", 10)
        )
        self.split_btn.pack(side='left', padx=5)
        
        # 선택된 파일 표시
        self.file_label = tk.Label(
            button_frame,
            text="선택된 파일: (없음)",
            anchor='w',
            bg="#f0f0f0",
            font=("Arial", 10)
        )
        self.file_label.pack(side='left', padx=10, fill='x', expand=True)
        
        # 중간: 옵션 프레임
        options_frame = tk.Frame(self, bg="#f0f0f0")
        options_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(
            options_frame,
            text="분리 간격 (초):",
            bg="#f0f0f0",
            font=("Arial", 10)
        ).pack(side='left', padx=5)
        
        self.interval_var = tk.StringVar(value="420")
        interval_entry = tk.Entry(
            options_frame,
            textvariable=self.interval_var,
            width=10,
            font=("Arial", 10)
        )
        interval_entry.pack(side='left', padx=5)
        
        tk.Label(
            options_frame,
            text="(기본: 420초 = 7분)",
            bg="#f0f0f0",
            font=("Arial", 9)
        ).pack(side='left', padx=5)
        
        # 하단: 로그 출력창
        log_label = tk.Label(
            self,
            text="처리 상태:",
            anchor='w',
            bg="#f0f0f0",
            font=("Arial", 10, "bold")
        )
        log_label.pack(pady=(10, 2), padx=10, fill='x')
        
        self.log_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            height=20,
            font=("Arial", 10),
            bg="#ffffff"
        )
        self.log_text.pack(padx=10, pady=(2, 10), expand=True, fill='both')
        self.log_text.config(state=tk.DISABLED)
    
    def select_mp3_file(self):
        """MP3 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="MP3 파일 선택",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.mp3_file = file_path
            self.output_dir = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"선택된 파일: {filename}")
            self.split_btn.config(state=tk.NORMAL)
            self.log(f"파일 선택됨: {filename}")
    
    def start_split(self):
        """파일 분리 시작 (multiprocessing 사용)"""
        if not self.mp3_file:
            messagebox.showerror("오류", "MP3 파일을 먼저 선택하세요.")
            return
        
        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                messagebox.showerror("오류", "분리 간격은 0 이상이어야 합니다.")
                return
        except ValueError:
            messagebox.showerror("오류", "분리 간격은 숫자여야 합니다.")
            return
        
        self.is_processing = True
        self.split_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Whisper 프로세스 시작
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=whisper_worker,
            args=(self.mp3_file, "tiny", self.queue)
        )
        self.process.start()
        
        # 상태 확인 시작
        self.log("=" * 50)
        self.log("파일 분리 시작...")
        self.log(f"입력 파일: {self.mp3_file}")
        self.log(f"분리 간격: {interval}초")
        self.log("=" * 50)
        self.log("\n1단계: MP3 파일에서 텍스트 추출 중...")
        self.log("⚠️  첫 실행 시 모델 다운로드로 시간이 소요될 수 있습니다...")
        
        self.after(500, self.check_whisper_process, interval)
    
    def check_whisper_process(self, interval):
        """Whisper 프로세스 상태 확인"""
        if self.queue is not None and not self.queue.empty():
            data = self.queue.get()
            if data["error"]:
                self.log(f"\n❌ 오류 발생: {data['error']}")
                messagebox.showerror("오류", f"Whisper 오류:\n{data['error']}")
                self.is_processing = False
                self.split_btn.config(state=tk.NORMAL)
                self.select_btn.config(state=tk.NORMAL)
                return
            
            # Whisper 완료 - 분할 처리 시작
            try:
                segments = data["result"]["segments"]
                self.log(f"✅ 추출 완료! ({len(segments)}개 세그먼트)")
                
                # 절단 지점 찾기
                self.log(f"\n2단계: 절단 지점 찾는 중 ({interval}초 간격)...")
                split_points = self._find_split_points(segments, interval)
                self.log(f"✅ {len(split_points) - 1}개 부분으로 분리합니다.")
                
                # 오디오 분리
                self.log("\n3단계: 오디오 파일 분리 중...")
                self._split_audio_by_context(self.mp3_file, split_points)
                
                self.log("\n" + "=" * 50)
                self.log("✅ 파일 분리 완료!")
                self.log(f"📁 저장 위치: {self.output_dir}")
                self.log("=" * 50)
                messagebox.showinfo("완료", "파일 분리가 완료되었습니다!")
                
            except Exception as e:
                error_msg = f"❌ 오류 발생: {str(e)}"
                self.log("\n" + error_msg)
                messagebox.showerror("오류", f"파일 분리 중 오류:\n{str(e)}")
            
            finally:
                self.is_processing = False
                self.split_btn.config(state=tk.NORMAL)
                self.select_btn.config(state=tk.NORMAL)
        else:
            # 프로세스 아직 실행 중
            if self.process.is_alive():
                self.after(500, self.check_whisper_process, interval)
    
    def _find_split_points(self, segments, target_interval_sec):
        """문맥상 자를 지점 결정"""
        split_points = [0]
        last_split = 0
        
        for segment in segments:
            if segment['end'] - last_split >= target_interval_sec:
                split_points.append(segment['end'] * 1000)  # 밀리초 단위
                last_split = segment['end']
                minutes = int(segment['end'] / 60)
                seconds = int(segment['end'] % 60)
                self.log(f"  절단점 찾음: {minutes}분 {seconds}초")
        
        return split_points
    
    def _split_audio_by_context(self, audio_path, split_points):
        """오디오 자르기 및 저장 (FFmpeg 사용 - 고속 메모리 효율)"""
        input_name = os.path.basename(audio_path).split('.')[0]
        
        for i in range(len(split_points) - 1):
            start_ms = split_points[i]
            end_ms = split_points[i + 1]
            duration_ms = end_ms - start_ms
            
            start_sec = start_ms / 1000.0
            duration_sec = duration_ms / 1000.0
            
            outfile = os.path.join(self.output_dir, f"{input_name}_part_{i+1}.mp3")
            
            # FFmpeg으로 고속 처리
            try:
                cmd = [
                    'ffmpeg',
                    '-i', audio_path,
                    '-ss', str(start_sec),
                    '-t', str(duration_sec),
                    '-q:a', '5',  # 음질 유지하면서 빠른 처리
                    '-y',  # 기존 파일 덮어쓰기
                    outfile
                ]
                
                subprocess.run(cmd, capture_output=True, check=True)
                
                start_min = int(start_ms / 1000 / 60)
                start_sec_int = int((start_ms / 1000) % 60)
                end_min = int(end_ms / 1000 / 60)
                end_sec_int = int((end_ms / 1000) % 60)
                
                self.log(f"  Part {i+1} 저장 완료: {start_min}분{start_sec_int}초 ~ {end_min}분{end_sec_int}초")
            except subprocess.CalledProcessError as e:
                error_msg = f"FFmpeg 오류 (Part {i+1}): {e.stderr.decode('utf-8', errors='ignore')}"
                self.log(f"  ❌ {error_msg}")
                raise Exception(error_msg)
            except FileNotFoundError:
                error_msg = "ffmpeg이 설치되지 않았습니다. 'brew install ffmpeg' 실행하세요."
                self.log(f"  ❌ {error_msg}")
                raise Exception(error_msg)
    
    def log(self, message):
        """로그 메시지 출력"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()
