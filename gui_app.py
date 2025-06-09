import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

from convert_view import ConvertView
from study_loading_view import StudyWithLoadingView

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("lernenMP3 - MP3 Conversion and Study Tool")
        self.geometry("1000x800")

        notebook = ttk.Notebook(self)
        self.convert_view = ConvertView(notebook)
        self.study_loading_view = StudyWithLoadingView(notebook)
        # 탭을 Notebook에 추가
        notebook.add(self.convert_view, text="Convert")
        notebook.add(self.study_loading_view, text="Study (Extracted/Pre-extracted)")
        notebook.pack(expand=True, fill='both')

        # 메뉴 예시 (공통 메뉴)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open MP3 File", command=self.convert_view.open_file)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        # Called when the tab is changed
        current_tab = event.widget.tab(event.widget.select(), "text")
        if current_tab == "Study":
            # When the "Study" tab is selected, check if there is a conversion result
            if not self.convert_view.last_result:
                messagebox.showwarning("Warning", "No conversion result found.\nPlease run conversion in the 'Convert' tab first.")
                # Automatically switch to the "Convert" tab
                event.widget.select(self.convert_view)
            else:
                # 변환 결과가 있으면 StudyView에 데이터 전달
                self.study_view.load_segments(
                    self.convert_view.last_result["segments"],
                    self.convert_view.mp3_file,
                    self.convert_view.ko_sentences
                )
        elif current_tab == "공부하기(기추출)":
            # 변환 결과가 있고, 아직 파일이 로드되지 않았다면 자동 로드
            if (self.convert_view.last_result and
                self.convert_view.mp3_file and
                hasattr(self.study_loading_view, "mp3_path") and
                not self.study_loading_view.mp3_path):
                base = os.path.splitext(self.convert_view.mp3_file)[0]
                de_srt_path = base + ".srt"
                ko_srt_path = base + "_ko.srt"
                # StudyWithLoadingView의 load_files 호출
                self.study_loading_view.load_files(
                    self.convert_view.mp3_file,
                    de_srt_path,
                    ko_srt_path
                )

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
