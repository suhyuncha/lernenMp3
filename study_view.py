import tkinter as tk
from pydub import AudioSegment
import pygame
import os
from base_study_view import BaseStudyView


class StudyView(BaseStudyView):
    def __init__(self, parent):
        super().__init__(parent, use_textbox=True)
        # BaseStudyView에서 text_box, tag_configure, 클릭 바인딩 모두 처리하므로 여기서 따로 생성/바인딩 불필요

    def load_segments(self, segments, audio_path, ko_sentences):
        # BaseStudyView의 show_segments를 그대로 사용하면 됨
        self.show_segments(segments, audio_path, ko_sentences)

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
            #print(f"재생할 세그먼트: {seg_idx + 1}, 시작: {seg['start']}, 종료: {seg['end']}")
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
