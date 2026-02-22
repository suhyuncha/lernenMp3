import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

from split_view import SplitView
from convert_view import ConvertView
from study_loading_view import StudyWithLoadingView

class MainApp(tk.Tk):
    def __init__(self):
        """
        Initialize the main application window for lernenMP3.

        Sets up the main window properties, including title and size.
        Creates a tabbed interface (Notebook) with two tabs:
            - Convert: For MP3 file conversion.
            - Study (Extracted/Pre-extracted): For studying with extracted or pre-extracted content.
        Adds a menu bar with options to open an MP3 file and exit the application.
        Binds a handler to the tab change event.

        Attributes:
            convert_view (ConvertView): The view for MP3 conversion.
            study_loading_view (StudyWithLoadingView): The view for studying with extracted/pre-extracted content.
        """
        super().__init__()
        self.title("lernenMP3 - MP3 Conversion and Study Tool")
        self.geometry("1000x800")

        notebook = ttk.Notebook(self)
        self.split_view = SplitView(notebook)
        self.convert_view = ConvertView(notebook)
        self.study_loading_view = StudyWithLoadingView(notebook)
        # Add tabs to the Notebook
        notebook.add(self.split_view, text="Split")
        notebook.add(self.convert_view, text="Convert")
        notebook.add(self.study_loading_view, text="Study (Extracted/Pre-extracted)")
        notebook.pack(expand=True, fill='both')

        # Example menu (common menu)
        menubar = tk.Menu(self)
        self.filemenu = tk.Menu(menubar, tearoff=0)
        self.filemenu.add_command(label="Open MP3 File", command=self.convert_view.open_file)

        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=self.filemenu)
        self.config(menu=menubar)
        
        # notebook 참조 저장
        self.notebook = notebook

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        # Called when the tab is changed
        current_tab = event.widget.tab(event.widget.select(), "text")
        
        # Menu 상태 관리: Study 탭에서는 "Open MP3 File" 메뉴 비활성화
        if current_tab == "Study (Extracted/Pre-extracted)":
            self.filemenu.entryconfig(0, state=tk.DISABLED)
        else:
            self.filemenu.entryconfig(0, state=tk.NORMAL)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
