import tkinter as tk
from tkinter import ttk
import tkinterdnd2 as tkdnd

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