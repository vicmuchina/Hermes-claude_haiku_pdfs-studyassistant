import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinterdnd2 as tkdnd
import fitz
from PIL import Image, ImageTk
import queue
import threading

from ui_components import setup_initial_ui, setup_main_ui
from pdf_utils import load_pdf, display_page, get_adjusted_coords
from ai_handler import start_ai_thread, ai_worker

class PDFStudyAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Study Assistant")
        self.root.geometry("1000x600")
        self.root.pack_propagate(False)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.messages = [
            {"role": "system", "content": "You are a helpful study assistant. Analyze the PDF content and answer questions about it."}
        ]
        self.pdf_canvas = None
        self.line_numbers = None
        self.selected_text = ""
        self.is_highlighting = False
        self.highlight_start = None
        self.highlighted_text = ""
        self.current_pdf = None
        self.current_page = 0
        self.page_cache = {}
        self.ai_queue = queue.Queue()

        setup_initial_ui(self)
        start_ai_thread(self)

    # ... (other methods from the original PDFStudyAssistant class)

    def browse_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            load_pdf(self, file_path)

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith('.pdf'):
            load_pdf(self, file_path)
        else:
            messagebox.showerror("Error", "Please drop a PDF file.")

    # ... (other methods from the original PDFStudyAssistant class)