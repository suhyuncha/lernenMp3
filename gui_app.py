from convert_view import ConvertView
from study_view import StudyView
from study_loading_view import StudyWithLoadingView
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP3 → 텍스트 변환기")
        self.geometry("1000x800")

        # 탭을 아래로 배치(tabposition="s")
        notebook = ttk.Notebook(self)
        self.convert_view = ConvertView(notebook)
        self.study_view = StudyView(notebook)
        self.study_loading_view = StudyWithLoadingView(notebook)
        # 탭을 Notebook에 추가
        notebook.add(self.convert_view, text="변환하기")
        notebook.add(self.study_view, text="공부하기")
        notebook.add(self.study_loading_view, text="공부하기(기추출)")
        notebook.pack(expand=True, fill='both')

        # 메뉴 예시 (공통 메뉴)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="MP3 파일 열기", command=self.convert_view.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="종료", command=self.quit)
        menubar.add_cascade(label="파일", menu=filemenu)
        self.config(menu=menubar)

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        # 탭이 변경될 때 호출되는 메서드
        current_tab = event.widget.tab(event.widget.select(), "text")
        if current_tab == "공부하기":
            # "공부하기" 탭이 선택되면, 변환 결과가 있는지 확인
            if not self.convert_view.last_result:
                messagebox.showwarning("경고", "변환 결과가 없습니다.\n먼저 '변환하기' 탭에서 변환을 진행하세요.")
                # "변환하기" 탭으로 자동 전환
                event.widget.select(self.convert_view)
            else:
                # 변환 결과가 있으면 StudyView에 데이터 전달
                self.study_view.load_segments(
                    self.convert_view.last_result["segments"],
                    self.convert_view.mp3_file,
                    self.convert_view.ko_sentences
                )

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
