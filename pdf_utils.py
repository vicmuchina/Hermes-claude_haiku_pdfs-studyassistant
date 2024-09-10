import fitz
from PIL import Image, ImageTk
import pytesseract
from tkinter import messagebox
import tkinter as tk

def load_pdf(self, file_path):
    try:
        self.current_pdf = fitz.open(file_path)
        self.current_page = 0
        self.page_cache = {}
        self.setup_main_ui()
        display_page(self)
        self.submit_pdf_button.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "PDF loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error loading PDF: {str(e)}")

def display_page(self):
    if self.current_pdf and self.pdf_canvas:
        if self.current_page in self.page_cache:
            photo, text = self.page_cache[self.current_page]
        else:
            page = self.current_pdf[self.current_page]
            self.scale_factor = 2  # Increase resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            
            # Perform OCR on the page image
            text = pytesseract.image_to_string(img)
            
            self.page_cache[self.current_page] = (photo, text)

        self.pdf_canvas.delete("all")
        self.pdf_canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))
        self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.pdf_canvas.image = photo  # Keep a reference

        update_line_numbers(self, text)

def get_adjusted_coords(self, x, y):
    canvas_x = self.pdf_canvas.canvasx(x)
    canvas_y = self.pdf_canvas.canvasy(y)
    return canvas_x, canvas_y

def update_line_numbers(self, text):
    lines = text.split('\n')
    line_numbers = '\n'.join(str(i) for i in range(1, len(lines) + 1))
    self.line_numbers.config(state='normal')
    self.line_numbers.delete('1.0', tk.END)
    self.line_numbers.insert('1.0', line_numbers)
    self.line_numbers.config(state='disabled')

def get_page_text(self, page_num):
    if page_num in self.page_cache:
        _, text = self.page_cache[page_num]
    else:
        page = self.current_pdf[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
    return text