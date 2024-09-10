import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinterdnd2 as tkdnd
import fitz
from PIL import Image, ImageTk
import queue
import threading

from ui_components import setup_initial_ui, setup_main_ui
from pdf_utils import load_pdf, display_page, get_adjusted_coords, get_page_text
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

    def end_selection(self, event):
        if self.selection_start:
            x0, y0 = self.selection_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            rect = fitz.Rect(min(x0, x1)/self.scale_factor, min(y0, y1)/self.scale_factor, 
                            max(x0, x1)/self.scale_factor, max(y0, y1)/self.scale_factor)
            
            # Use the cached text from OCR instead of getting it directly from the PDF
            _, page_text = self.page_cache[self.current_page]
            lines = page_text.split('\n')
            
            # Calculate the selected text based on the selection coordinates
            start_line = int(rect.y0 / (self.pdf_canvas.winfo_height() / len(lines)))
            end_line = int(rect.y1 / (self.pdf_canvas.winfo_height() / len(lines)))
            self.selected_text = '\n'.join(lines[start_line:end_line+1])
            
            if self.selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.selected_text)
                messagebox.showinfo("Text Copied", "Selected text has been copied to clipboard!")
            
            print(f"Selected text: {self.selected_text}")
            self.selection_start = None
            self.pdf_canvas.delete("selection")  # Remove the selection rectangle after copying

    def submit_pdf_to_ai(self):
        # Submit entire PDF content to AI for analysis
        if self.current_pdf:
            full_text = ""
            for page_num in range(len(self.current_pdf)):
                full_text += get_page_text(self, page_num) + "\n"
            self.ai_queue.put(("pdf", full_text))

    # ... (other methods from the original PDFStudyAssistant class)