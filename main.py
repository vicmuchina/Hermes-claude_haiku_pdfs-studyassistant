# Import necessary libraries
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import tkinterdnd2 as tkdnd  # For drag and drop functionality
import fitz  # PyMuPDF for PDF handling
from PIL import Image, ImageTk  # For image processing
import io
import requests
from openai import OpenAI
from os import getenv
import pytesseract  # For OCR (Optical Character Recognition)
import pyperclip
import threading
import queue

# Function to get model information from OpenRouter API
def get_model_info(model_name):
    response = requests.get(
        'https://openrouter.ai/api/v1/models',
        headers={'Authorization': f'Bearer {getenv("OPENROUTER_API_KEY")}'}
    )
    models = response.json()
    for model in models['data']:
        if model['id'] == model_name:
            return model
    return None

# Set up OpenAI client with OpenRouter base URL and API key
model = "mattshumer/reflection-70b:free"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)

# Get model info and set max tokens
model_info = get_model_info(model)
max_tokens = model_info['context_length'] if model_info else 131072

# Function to send completion request to the AI model
def completion(messages):
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return completion.choices[0].message.content

# Main application class
class PDFStudyAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Study Assistant")
        self.root.geometry("1000x600")  # Set a default size
        self.root.pack_propagate(False)  # Prevent automatic resizing

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize conversation with system message
        self.messages = [
            {"role": "system", "content": "You are a helpful study assistant. Analyze the PDF content and answer questions about it."}
        ]
        self.pdf_canvas = None  # Initialize it as None
        self.setup_initial_ui()
        self.line_numbers = None
        self.selected_text = ""
        self.is_highlighting = False
        self.highlight_start = None
        self.highlighted_text = ""
        self.current_pdf = None
        self.current_page = 0
        self.page_cache = {}
        self.highlighted_text = ""
        self.ai_queue = queue.Queue()
        self.start_ai_thread()

    def setup_initial_ui(self):
        self.initial_frame = ttk.Frame(self.main_frame)
        self.initial_frame.pack(fill=tk.BOTH, expand=True)

        self.browse_button = ttk.Button(self.initial_frame, text="Browse PDF", command=self.browse_pdf)
        self.browse_button.pack(pady=10)

        self.drop_label = ttk.Label(self.initial_frame, text="Or drag and drop PDF here")
        self.drop_label.pack(pady=10)

        self.drop_area = ttk.Frame(self.initial_frame, width=200, height=100, relief="groove", borderwidth=2)
        self.drop_area.pack(pady=10)

        self.drop_area.drop_target_register(tkdnd.DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

    def setup_main_ui(self):
        # Clear initial UI
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create a PanedWindow
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel for PDF viewer
        self.left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_panel, stretch="always")

        # Line numbers on the left
        self.line_numbers = tk.Text(self.left_panel, width=4, padx=5, pady=5, state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Create pdf_canvas
        self.pdf_canvas = tk.Canvas(self.left_panel, bg='white')
        self.pdf_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for PDF canvas
        self.pdf_scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.pdf_canvas.yview)
        self.pdf_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pdf_canvas.configure(yscrollcommand=self.pdf_scrollbar.set)

        # Right panel for AI chat
        self.right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_panel, stretch="always")
        
        self.chat_history = tk.Text(self.right_panel, wrap=tk.WORD, state='disabled')
        self.chat_history.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.chat_scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=self.chat_history.yview)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.configure(yscrollcommand=self.chat_scrollbar.set)

        self.input_frame = ttk.Frame(self.right_panel)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.user_input = ttk.Entry(self.input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Toolbar at the bottom
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add toolbar buttons here (browse, highlight, submit, etc.)
        self.browse_button = ttk.Button(self.toolbar, text="Browse PDF", command=self.browse_pdf)
        self.browse_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.highlight_button = ttk.Button(self.toolbar, text="Highlight", command=self.toggle_highlight_mode)
        self.highlight_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.submit_highlight_button = ttk.Button(self.toolbar, text="Submit Highlighted Text", command=self.submit_highlighted_text, state=tk.DISABLED)
        self.submit_highlight_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.submit_pdf_button = ttk.Button(self.toolbar, text="Submit PDF to AI", command=self.submit_pdf_to_ai, state=tk.DISABLED)
        self.submit_pdf_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_page_button = ttk.Button(self.toolbar, text="Previous Page", command=self.prev_page)
        self.prev_page_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.next_page_button = ttk.Button(self.toolbar, text="Next Page", command=self.next_page)
        self.next_page_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_ai_button = ttk.Button(self.toolbar, text="Toggle AI", command=self.toggle_ai_panel)
        self.toggle_ai_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Set up drag and drop for the main window
        self.root.drop_target_register(tkdnd.DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Setup selection bindings
        self.setup_selection_bindings()

    def setup_selection_bindings(self):
        self.pdf_canvas.bind("<ButtonPress-1>", self.start_selection)
        self.pdf_canvas.bind("<B1-Motion>", self.update_selection)
        self.pdf_canvas.bind("<ButtonRelease-1>", self.end_selection)
    def remove_selection_bindings(self):
        self.pdf_canvas.unbind("<ButtonPress-1>")
        self.pdf_canvas.unbind("<B1-Motion>")
        self.pdf_canvas.unbind("<ButtonRelease-1>")

    def on_drop(self, event):
        # Handle file drop event
        file_path = event.data
        if file_path.lower().endswith('.pdf'):
            self.load_pdf(file_path)
        else:
            messagebox.showerror("Error", "Please drop a PDF file.")
        
    def start_selection(self, event):
        x, y = self.get_adjusted_coords(event.x, event.y)
        self.selection_start = (x, y)

    def update_selection(self, event):
        if self.selection_start:
            self.pdf_canvas.delete("selection")
            x0, y0 = self.selection_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            self.pdf_canvas.create_rectangle(x0, y0, x1, y1, outline="blue", tags="selection")

    def end_selection(self, event):
        if self.selection_start:
            x0, y0 = self.selection_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            page = self.current_pdf[self.current_page]
            rect = fitz.Rect(min(x0, x1)/self.scale_factor, min(y0, y1)/self.scale_factor, 
                            max(x0, x1)/self.scale_factor, max(y0, y1)/self.scale_factor)
            self.selected_text = page.get_text("text", clip=rect)
            
            if self.selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.selected_text)
                messagebox.showinfo("Text Copied", "Selected text has been copied to clipboard!")
            
            print(f"Selected text: {self.selected_text}")
            self.selection_start = None
            self.pdf_canvas.delete("selection")  # Remove the selection rectangle after copying

    def copy_selected_text(self):
        if self.selected_text:
            pyperclip.copy(self.selected_text)
            print("Text copied to clipboard")
        else:
            print("No text selected")
    

    def browse_pdf(self):
        # Open file dialog to select PDF
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        try:
            self.current_pdf = fitz.open(file_path)
            self.current_page = 0
            self.page_cache = {}
            self.setup_main_ui()
            self.display_page()
            self.submit_pdf_button.config(state=tk.NORMAL)
            messagebox.showinfo("Success", "PDF loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading PDF: {str(e)}")

        
    def get_adjusted_coords(self, x, y):
        canvas_x = self.pdf_canvas.canvasx(x)
        canvas_y = self.pdf_canvas.canvasy(y)
        return canvas_x, canvas_y

    def display_page(self):
        if self.current_pdf and self.pdf_canvas:
            if self.current_page in self.page_cache:
                photo = self.page_cache[self.current_page]
            else:
                page = self.current_pdf[self.current_page]
                self.scale_factor = 2  # Increase resolution
                pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                self.page_cache[self.current_page] = photo

            self.pdf_canvas.delete("all")
            self.pdf_canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))
            self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.pdf_canvas.image = photo  # Keep a reference

            self.update_line_numbers()


    def update_line_numbers(self):
        # Update line numbers for the current page
        page = self.current_pdf[self.current_page]
        text = page.get_text("text")
        lines = text.split('\n')
        line_numbers = '\n'.join(str(i) for i in range(1, len(lines) + 1))
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_numbers)
        self.line_numbers.config(state='disabled')

    def toggle_highlight_mode(self):
        # Toggle text highlighting mode
        self.is_highlighting = not self.is_highlighting
        self.highlight_button.config(text="Stop Highlighting" if self.is_highlighting else "Highlight")
        if self.is_highlighting:
            self.remove_selection_bindings()  # Remove selection bindings
            self.pdf_canvas.bind("<ButtonPress-1>", self.start_highlight)
            self.pdf_canvas.bind("<B1-Motion>", self.update_highlight)
            self.pdf_canvas.bind("<ButtonRelease-1>", self.end_highlight)
        else:
            self.pdf_canvas.unbind("<ButtonPress-1>")
            self.pdf_canvas.unbind("<B1-Motion>")
            self.pdf_canvas.unbind("<ButtonRelease-1>")
            self.setup_selection_bindings()  # Restore selection bindings

    def start_highlight(self, event):
        # Start the highlighting process
        self.highlight_start = (event.x, event.y)

    def update_highlight(self, event):
        # Update the highlight rectangle as the user drags the mouse
        if self.highlight_start:
            self.pdf_canvas.delete("highlight")
            x0, y0 = self.highlight_start
            x1, y1 = event.x, event.y
            self.pdf_canvas.create_rectangle(x0, y0, x1, y1, outline="yellow", fill="yellow", stipple="gray50", tags="highlight")

    def end_highlight(self, event):
        if self.highlight_start:
            x0, y0 = self.highlight_start
            x1, y1 = event.x, event.y
            page = self.current_pdf[self.current_page]
            rect = fitz.Rect(min(x0, x1)/self.scale_factor, min(y0, y1)/self.scale_factor, 
                            max(x0, x1)/self.scale_factor, max(y0, y1)/self.scale_factor)
            words = page.get_text("words")
            self.highlighted_text = " ".join(w[4] for w in words if fitz.Rect(w[:4]).intersects(rect))
            self.highlight_start = None
        
        if self.highlighted_text:
            self.submit_highlight_button.config(state=tk.NORMAL)
            self.root.clipboard_clear()
            self.root.clipboard_append(self.highlighted_text)
            messagebox.showinfo("Highlight", "Text highlighted and copied to clipboard!")

    def submit_highlighted_text(self):
        # Submit highlighted text to AI for analysis
        if self.highlighted_text:
            self.ai_queue.put(("highlight", self.highlighted_text))
            self.highlighted_text = ""
            self.submit_highlight_button.config(state=tk.DISABLED)

    def submit_pdf_to_ai(self):
        # Submit entire PDF content to AI for analysis
        if self.current_pdf:
            full_text = ""
            for page in self.current_pdf:
                full_text += page.get_text()
            self.ai_queue.put(("pdf", full_text))

    def send_message(self):
        # Send user message to AI
        user_message = self.user_input.get()
        self.update_chat_history(f"You: {user_message}\n")
        self.ai_queue.put(("message", user_message))
        self.user_input.delete(0, tk.END)

    def update_chat_history(self, message):
        # Update chat history with new messages
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, message)
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

    def toggle_ai_panel(self):
        if self.right_panel.winfo_viewable():
            self.paned_window.forget(self.right_panel)
            self.toggle_ai_button.config(text="Show AI")
        else:
            self.paned_window.add(self.right_panel)  # Remove the weight parameter
            self.toggle_ai_button.config(text="Hide AI")
        self.paned_window.update()

        
    def prev_page(self):
        # Go to previous page of PDF
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        # Go to next page of PDF
        if self.current_pdf and self.current_page < len(self.current_pdf) - 1:
            self.current_page += 1
            self.display_page()

    def change_font(self, *args):
        # Change font of chat history
        selected_font = self.font_var.get()
        selected_size = self.font_size_var.get()
        new_font = font.Font(family=selected_font, size=selected_size)
        self.chat_history.configure(font=new_font)

    def start_ai_thread(self):
        # Start a separate thread for AI processing
        threading.Thread(target=self.ai_worker, daemon=True).start()

    def ai_worker(self):
        # Worker function for AI processing thread
        while True:
            task_type, content = self.ai_queue.get()
            if task_type == "highlight":
                self.messages.append({"role": "user", "content": f"Analyze this highlighted text: {content}"})
            elif task_type == "message":
                self.messages.append({"role": "user", "content": content})
            elif task_type == "pdf":
                self.messages.append({"role": "user", "content": f"Here's the full content of the PDF: {content[:1000]}... [truncated]"})
            
            response = completion(self.messages)
            self.messages.append({"role": "assistant", "content": response})
            self.root.after(0, self.update_chat_history, f"AI: {response}\n")
            self.ai_queue.task_done()

def main():
    root = tkdnd.TkinterDnD.Tk()
    app = PDFStudyAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()