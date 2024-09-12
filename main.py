# Import necessary libraries
import tkinter as tk  # (GUI toolkit for creating desktop applications)
# ttk (themed tk) is a module in tkinter that provides access to the Tk themed widget set,
# offering a more modern and customizable look for GUI elements compared to standard tkinter widgets
from tkinter import ttk, filedialog, messagebox, font as tkfont
# Example: ttk.Button(parent, text="Click me") creates a themed button
import tkinterdnd2 as tkdnd  # (Extension for drag and drop functionality)
# Example: root.drop_target_register(tkdnd.DND_FILES) enables file drop on a window
import fitz  # (PyMuPDF library for PDF handling)
# Example: doc = fitz.open("example.pdf") opens a PDF file
from PIL import Image, ImageTk  # (Python Imaging Library for image processing)
# Example: img = Image.open("example.jpg") opens an image file
import io
import requests
from openai import OpenAI
from os import getenv
import pytesseract  # (Optical Character Recognition library)
# Example: text = pytesseract.image_to_string(Image.open('image.png')) extracts text from an image
import pyperclip
import threading
import queue
from duckduckgo_search import DDGS
import time
from openai import OpenAIError
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk
from pix2tex.cli import LatexOCR
import numpy as np

# Function to get model information from OpenRouter API
def get_model_info(model_name):
    """
    Retrieves information about a specific AI model from the OpenRouter API.
    
    This function sends a GET request (a way to request data from a server) to the OpenRouter API
    to fetch details about available models. It then searches for the specified model by name
    and returns its information.

    Parameters:
    - model_name (str): The name of the AI model to look up

    Returns:
    - dict or None: A dictionary (a data structure that stores key-value pairs) containing model
      information if found, None otherwise
    
    Example:
    model_info = get_model_info("gpt-3.5-turbo")
    if model_info:
        print(f"Model context length: {model_info['context_length']}")
    """
    # Send a GET request to the OpenRouter API
    response = requests.get(
        'https://openrouter.ai/api/v1/models',
        headers={'Authorization': f'Bearer {getenv("OPENROUTER_API_KEY")}'}
    )
    models = response.json()
    
    # Search for the specified model in the response
    for model in models['data']:
        if model['id'] == model_name:
            return model
    return None

# Set up OpenAI client with OpenRouter base URL and API key
model = "nousresearch/hermes-3-llama-3.1-405b"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)

# Get model info and set max tokens
model_info = get_model_info(model)
max_tokens = model_info['context_length'] if model_info else 131072

# Function to send completion request to the AI model
def completion(messages, max_retries=3, retry_delay=5):
    """
    Sends a completion request to the AI model and returns the response.

    This function uses the OpenAI client (a tool for interacting with the AI model) to create
    a chat completion based on the provided messages. It then extracts and returns the content
    of the AI's response.

    Parameters:
    - messages (list): A list of message dictionaries to send to the AI

    Returns:
    - str: The content of the AI's response
    
    Example:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the capital of France?"}
    ]
    response = completion(messages)
    print(response)  # Outputs: "The capital of France is Paris."
    """
    """
    Sends a completion request to the AI model and returns the response.

    Parameters:
    - messages (list): A list of message dictionaries to send to the AI
    - max_retries (int): Maximum number of retry attempts
    - retry_delay (int): Delay in seconds between retry attempts

    Returns:
    - str: The content of the AI's response, or an error message
    """
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return completion.choices[0].message.content
        except OpenAIError as e:
            if attempt < max_retries - 1:
                print(f"Error occurred: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return f"Error: Unable to get a response from the AI after {max_retries} attempts. Please try again later."
        except Exception as e:
            return f"Unexpected error: {str(e)}"


# Main application class
class PDFStudyAssistant:
    def __init__(self, root):
        """
        Initializes the PDFStudyAssistant application.

        This method sets up the main window, initializes variables, and creates
        the initial user interface.

        Parameters:
        - root (tk.Tk): The root window (main window) of the application
        
        Example:
        root = tk.Tk()
        app = PDFStudyAssistant(root)
        """
        self.root = root
        self.root.title("PDF Study Assistant")
        self.root.geometry("1000x600")  # Set a default size
        self.root.pack_propagate(False)  # Prevent automatic resizing

        # Create the main frame (a container for other widgets)
        # ttk.Frame is a themed container widget used to group other widgets
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize conversation with system message
        self.messages = [
            {"role": "system", "content": "You are a helpful study assistant with the ability to analyze PDF content and answer questions about it. You can also perform web searches to gather additional information. When you need to search the web, simply include '/search' followed by your query in your response. For example, if you need to find information about climate change, you could say 'Let me search for more information. /search latest research on climate change'. Use this search capability when you need to provide up-to-date information or when the context from the PDF is insufficient to answer a question comprehensively. If the initial search results don't contain the exact information needed, you can perform a subsequent search using one of the links provided in the previous search results. For instance, you might say 'Let me check one of the provided links for more specific information. /search https://example.com specific query'. This allows you to dig deeper into reliable sources for more detailed or precise information. Remember, do not include square brackets in your search queries."}
        ]
        
        # Initialize various attributes
        self.pdf_canvas = None  # (A widget for displaying graphics)
        self.line_numbers = None
        self.selected_text = ""
        self.is_highlighting = False
        self.highlight_start = None
        self.highlighted_text = ""
        self.highlight_rectangle = None
        self.selection_start = None
        self.selection_rectangle = None

        self.current_pdf = None
        self.latex_ocr = LatexOCR()

        self.ddgs = DDGS()
        self.chat_model = "claude-3-haiku"  # You can change this to any of the available models
        self.current_page = 0
        self.page_cache = {}  # (A dictionary to store rendered pages for quick access)
        
        # Set up the initial UI and AI processing queue
        self.ai_queue = queue.Queue()  # (A thread-safe data structure for communication between threads)
        self.setup_initial_ui()
        self.start_ai_thread()

    def setup_initial_ui(self):
        """
        Sets up the initial user interface for the application.

        This method creates the initial frame with buttons and labels for
        browsing or dragging and dropping a PDF file.
        
        Example:
        self.setup_initial_ui()
        # This creates the initial UI with a "Browse PDF" button and a drop area
        """
        # Create the initial frame (a container for widgets)
        self.initial_frame = ttk.Frame(self.main_frame)
        self.initial_frame.pack(fill=tk.BOTH, expand=True)

        # Add a button to browse for PDF files
        # ttk.Button creates a themed button widget
        self.browse_button = ttk.Button(self.initial_frame, text="Browse PDF", command=self.browse_pdf)
        self.browse_button.pack(pady=10)

        # Add a label for drag and drop instructions
        # ttk.Label creates a themed label widget for displaying text
        self.drop_label = ttk.Label(self.initial_frame, text="Or drag and drop PDF here")
        self.drop_label.pack(pady=10)

        # Create a drop area for drag and drop functionality
        self.drop_area = ttk.Frame(self.initial_frame, width=200, height=100, relief="groove", borderwidth=2)
        self.drop_area.pack(pady=10)

        # Register the drop area for drag and drop events
        self.drop_area.drop_target_register(tkdnd.DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

    def setup_main_ui(self):
        """
        Sets up the main user interface of the application.

        This method is called after a PDF is loaded. It creates the PDF viewer,
        AI chat panel, and various controls for interacting with the PDF and AI.
        
        Example:
        self.setup_main_ui()
        # This creates the main UI with PDF viewer, chat panel, and controls
        """
        # Clear the initial UI
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create a PanedWindow (a widget that allows resizable panels)
        # tk.PanedWindow creates a widget with adjustable panes
        # Create a horizontal PanedWindow containing the PDF viewer and AI chat panel
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        # This PanedWindow will contain:
        # 1. Left panel: PDF viewer with line numbers, canvas, and scrollbar
        # 2. Right panel: AI chat interface with chat history, input field, and send button
        # tk.BOTH is used to fill the widget both horizontally and vertically
        # expand=True allows the widget to grow if extra space is available
        # Example: This makes the paned_window fill its parent container completely
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Set up the left panel for PDF viewing
        self.left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_panel, stretch="always")

        # Add line numbers to the left of the PDF viewer
        # tk.Text creates a text widget for displaying multiple lines of text
        self.line_numbers = tk.Text(self.left_panel, width=4, padx=5, pady=5, state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)  # fill=tk.Y means the widget will expand vertically to fill its container

        # Create the PDF canvas (a widget for displaying the PDF pages)
        # tk.Canvas creates a drawing area for graphics and images
        self.pdf_canvas = tk.Canvas(self.left_panel, bg='white')
        self.pdf_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar for the PDF canvas
        # ttk.Scrollbar creates a themed scrollbar widget
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL, command=self.pdf_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.HORIZONTAL, command=self.pdf_canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.pdf_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Bind mouse wheel event to the canvas
        self.pdf_canvas.bind("<MouseWheel>", self.on_mousewheel)  # For Windows and MacOS
        self.pdf_canvas.bind("<Button-4>", self.on_mousewheel)    # For Linux
        self.pdf_canvas.bind("<Button-5>", self.on_mousewheel)    # For Linux


        # Set up the right panel for AI chat
        self.right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_panel, stretch="always")
        
        # Create a text widget for chat history
        self.chat_history = tk.Text(self.right_panel, wrap=tk.WORD, state='disabled')
        self.chat_history.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.chat_history.images = []


        # Add a scrollbar for the chat history
        self.chat_scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=self.chat_history.yview)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.configure(yscrollcommand=self.chat_scrollbar.set)

        # Create an input frame for user messages
        self.input_frame = ttk.Frame(self.right_panel)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Add an entry widget (a single-line text input field) for user input
        # ttk.Entry creates a themed single-line texIt input widget
        self.user_input = ttk.Entry(self.input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Add a send button for user messages
        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Create a toolbar (a frame with buttons) at the bottom of the window
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add various buttons to the toolbar
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

        # Add font selection options
        self.setup_font_options()

        # Set up drag and drop for the main window
        self.root.drop_target_register(tkdnd.DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Setup selection bindings for text selection in the PDF
        self.setup_selection_bindings()

    def setup_font_options(self):
        """
        Sets up the font selection options in the toolbar.
        """
        # Get a list of available fonts
        self.available_fonts = sorted(tkfont.families())
        
        # Create variables to store the selected font and size
        self.font_var = tk.StringVar(self.root)
        self.font_var.set("TkDefaultFont")  # Set default font
        self.font_size_var = tk.StringVar(self.root)
        self.font_size_var.set("10")  # Set default font size
        
        # Create font selection dropdown
        self.font_menu = ttk.Combobox(self.toolbar, textvariable=self.font_var, values=self.available_fonts, width=15)
        self.font_menu.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Create font size dropdown
        font_sizes = [str(i) for i in range(8, 25)]
        self.font_size_menu = ttk.Combobox(self.toolbar, textvariable=self.font_size_var, values=font_sizes, width=3)
        self.font_size_menu.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Bind the selection events to the change_font method
        self.font_menu.bind("<<ComboboxSelected>>", self.change_font)
        self.font_size_menu.bind("<<ComboboxSelected>>", self.change_font)

    def change_font(self, *args):
        """
        Changes the font of the chat history.
        """
        selected_font = self.font_var.get()
        selected_size = int(self.font_size_var.get())
        new_font = tkfont.Font(family=selected_font, size=selected_size)
        self.chat_history.configure(font=new_font)

    def setup_selection_bindings(self):
        """
        Sets up event bindings for text selection in the PDF.

        This method binds the necessary events to enable text selection and
        copying in the PDF viewer.
        
        Example:
        self.setup_selection_bindings()
        # This enables text selection in the PDF viewer
        """
        self.pdf_canvas.bind("<ButtonPress-1>", self.start_selection)
        self.pdf_canvas.bind("<B1-Motion>", self.update_selection)
        self.pdf_canvas.bind("<ButtonRelease-1>", self.end_selection)

    def remove_selection_bindings(self):
        """
        Removes event bindings for text selection in the PDF.

        This method unbinds the events that enable text selection and copying
        in the PDF viewer.
        """
        self.pdf_canvas.unbind("<ButtonPress-1>")
        self.pdf_canvas.unbind("<B1-Motion>")
        self.pdf_canvas.unbind("<ButtonRelease-1>")

    def on_drop(self, event):
        """
        Handles the drop event for drag and drop functionality.

        This method is called when a file is dropped onto the drop area. It
        checks if the dropped file is a PDF and loads it if it is.

        Parameters:
        - event (tk.Event): The drop event
        """
        # Handle file drop event
        file_path = event.data
        if file_path.lower().endswith('.pdf'):
            self.load_pdf(file_path)
        else:
            messagebox.showerror("Error", "Please drop a PDF file.")
        
    def start_selection(self, event):
        """
        Starts the text selection process.

        This method is called when the user presses the mouse button to start
        selecting text in the PDF viewer.

        Parameters:
        - event (tk.Event): The mouse button press event
        """
        self.selection_start = self.get_adjusted_coords(event.x, event.y)

    def update_selection(self, event):
        """
        Updates the text selection rectangle as the user drags the mouse.

        This method is called while the user is dragging the mouse to update
        the selection rectangle in the PDF viewer.

        Parameters:
        - event (tk.Event): The mouse motion event
        """
        if self.selection_start:
            x0, y0 = self.selection_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            if self.selection_rectangle:
                self.pdf_canvas.delete(self.selection_rectangle)
            self.selection_rectangle = self.pdf_canvas.create_rectangle(x0, y0, x1, y1, outline="blue", fill="blue", stipple="gray50")

    def end_selection(self, event):
        """
        Ends the text selection process and copies the selected text.

        This method is called when the user releases the mouse button after
        selecting text in the PDF viewer. It extracts the selected text and
        copies it to the clipboard.

        Parameters:
        - event (tk.Event): The mouse button release event
        """
        if self.selection_start:
            x0, y0 = self.selection_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            page = self.current_pdf[self.current_page]
            # Create a rectangle (rect) in PDF coordinates
            # The scale_factor is used to convert from screen coordinates to PDF coordinates
            #
            # PDF coordinates:
            # - Origin (0,0) is at the bottom-left corner of the page
            # - Units are typically in points (1/72 of an inch)
            #
            # Screen coordinates:
            # - Origin (0,0) is at the top-left corner of the canvas
            # - Units are in pixels
            #
            # The scale_factor represents the ratio of screen pixels to PDF points
            # For example, if scale_factor is 2, it means 2 screen pixels = 1 PDF point
            #
            # We divide by scale_factor to convert from screen coordinates to PDF coordinates:
            # PDF_coordinate = screen_coordinate / scale_factor
            
            rect = fitz.Rect(
                min(x0, x1) / self.scale_factor,  # left (convert smaller x to PDF coordinate)
                min(y0, y1) / self.scale_factor,  # top (convert smaller y to PDF coordinate)
                max(x0, x1) / self.scale_factor,  # right (convert larger x to PDF coordinate)
                max(y0, y1) / self.scale_factor   # bottom (convert larger y to PDF coordinate)
            )

            # Debug print
            print(f"Selection rectangle: {rect}")
            print(f"Scale factor: {self.scale_factor}")
            
            words = page.get_text("words", clip=rect)
            text_block = page.get_text("block", clip=rect)
            text_raw = page.get_text("text", clip=rect)

            # Debug print
            print(f"Extracted words: {words}")
            print(f"Extracted text block: {text_block}")
            print(f"Extracted text raw: {text_raw}")
            
            
            selected_text = " ".join(w[4] for w in words)
            # If no text is extracted, try OCR
            if not selected_text.strip():
                # Extract image from the selected area
                pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor), clip=rect)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Perform OCR on the image
                selected_text = pytesseract.image_to_string(img)
            
            # Debug print
            print(f"Selected text: '{selected_text}'")
            
            if selected_text.strip():
                self.copy_to_clipboard(selected_text)
                messagebox.showinfo("Selection", "Text copied to clipboard!")
            else:
                 # Try getting text without clipping
                full_text = page.get_text("text")
                print(f"Full page text: {full_text[:100]}...")  # Print first 100 characters
                messagebox.showinfo("Selection", "No text selected.")

            self.selection_start = None
            if self.selection_rectangle:
                self.pdf_canvas.delete(self.selection_rectangle)
                self.selection_rectangle = None



    def copy_selected_text(self):
        """
        Copies the selected text to the clipboard.

        This method copies the currently selected text in the PDF viewer to
        the clipboard.
        """
        if self.selected_text:
            pyperclip.copy(self.selected_text)
            print("Text copied to clipboard")
        else:
            print("No text selected")
    

    def browse_pdf(self):
        """
        Opens a file dialog to browse and select a PDF file.

        This method is called when the user clicks the "Browse PDF" button.
        It opens a file dialog to allow the user to select a PDF file.
        """
        # Open file dialog to select PDF
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        """
        Loads a PDF file and sets up the main user interface.

        This method is called when a PDF file is selected or dropped. It loads
        the PDF file, initializes variables, and sets up the main user interface.

        Parameters:
        - file_path (str): The path to the PDF file
        """
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
        """
        Adjusts the mouse coordinates based on the PDF canvas scale.

        This method is used to convert mouse coordinates from the canvas
        to the PDF page coordinates, taking into account the scale factor.

        Parameters:
        - x (int): The x-coordinate on the canvas
        - y (int): The y-coordinate on the canvas

        Returns:
        - tuple: The adjusted (x, y) coordinates on the PDF page
        """
        canvas_x = self.pdf_canvas.canvasx(x)
        canvas_y = self.pdf_canvas.canvasy(y)
        return canvas_x, canvas_y

    def display_page(self):
        """
        Displays the current PDF page on the canvas.

        This method is called when the current page is changed or when the
        PDF is loaded. It renders the PDF page as an image and displays it
        on the canvas.
        """
        if self.current_pdf and self.pdf_canvas:
            if self.current_page in self.page_cache:
                photo = self.page_cache[self.current_page]
            else:
                page = self.current_pdf[self.current_page]
                # Set the scale factor to 2 to increase the resolution of the PDF page
                self.scale_factor = 2

                # Create a high-resolution pixmap (image) of the PDF page
                # The fitz.Matrix(2, 2) doubles the resolution in both x and y directions
                pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))

                # Convert the pixmap to a PIL (Python Imaging Library) Image
                # This step is necessary because Tkinter can't directly use the pixmap
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Convert the PIL Image to a Tkinter-compatible PhotoImage
                # This is the format that Tkinter can display on the canvas
                photo = ImageTk.PhotoImage(img)

                # Store the photo in the page cache for faster access in the future
                self.page_cache[self.current_page] = photo

            # Clear any existing content on the PDF canvas
            self.pdf_canvas.delete("all")

            # Set the scrollable region of the canvas to match the size of the photo
            # This ensures that scrollbars appear if the image is larger than the canvas
            self.pdf_canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))

            # Place the photo on the canvas at the top-left corner (0, 0)
            # 'anchor=tk.NW' means the image's northwest (top-left) corner will be at (0, 0)
            self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=photo)

            # Store a reference to the photo in the canvas object
            # This prevents the image from being garbage collected by Python
            self.pdf_canvas.image = photo

            # Update the line numbers displayed alongside the PDF
            self.update_line_numbers()

    def update_line_numbers(self):
        """
        Updates the line numbers for the current PDF page.

        This method is called when the current page is changed or when the
        PDF is loaded. It extracts the text from the PDF page and displays
        the line numbers on the left side of the PDF viewer.
        """
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
        """
        Toggles the text highlighting mode.

        This method is called when the user clicks the "Highlight" button.
        It toggles the text highlighting mode and updates the button text
        accordingly.
        """
        # Toggle text highlighting mode
        self.is_highlighting = not self.is_highlighting
        self.highlight_button.config(text="Stop Highlighting" if self.is_highlighting else "Highlight")
        if self.is_highlighting:
            self.remove_selection_bindings()
            self.pdf_canvas.bind("<ButtonPress-1>", self.start_highlight)
            self.pdf_canvas.bind("<B1-Motion>", self.update_highlight)
            self.pdf_canvas.bind("<ButtonRelease-1>", self.end_highlight)
        else:
            self.pdf_canvas.unbind("<ButtonPress-1>")
            self.pdf_canvas.unbind("<B1-Motion>")
            self.pdf_canvas.unbind("<ButtonRelease-1>")
            self.setup_selection_bindings()



    def start_highlight(self, event):
        """
        Starts the text highlighting process.

        This method is called when the user presses the mouse button to start
        highlighting text in the PDF viewer.

        Parameters:
        - event (tk.Event): The mouse button press event
        """
        # Start the highlighting process
        self.highlight_start = self.get_adjusted_coords(event.x, event.y)


    def update_highlight(self, event):
        """
        Updates the highlight rectangle as the user drags the mouse.

        This method is called while the user is dragging the mouse to update
        the highlight rectangle in the PDF viewer.

        Parameters:
        - event (tk.Event): The mouse motion event
        """
        # Update the highlight rectangle as the user drags the mouse
        if self.highlight_start:
            x0, y0 = self.highlight_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            if self.highlight_rectangle:
                self.pdf_canvas.delete(self.highlight_rectangle)
            self.highlight_rectangle = self.pdf_canvas.create_rectangle(x0, y0, x1, y1, outline="yellow", fill="yellow", stipple="gray50")



    def end_highlight(self, event):
        """
        Ends the text highlighting process and submits the highlighted text.

        This method is called when the user releases the mouse button after
        highlighting text in the PDF viewer. It extracts the highlighted text
        and submits it to the AI for analysis. If the highlighted area contains
        a mathematical equation, it attempts to convert it to LaTeX.

        Parameters:
        - event (tk.Event): The mouse button release event
        """
        if self.highlight_start:
            x0, y0 = self.highlight_start
            x1, y1 = self.get_adjusted_coords(event.x, event.y)
            page = self.current_pdf[self.current_page]
            rect = fitz.Rect(min(x0, x1)/self.scale_factor, min(y0, y1)/self.scale_factor, 
                            max(x0, x1)/self.scale_factor, max(y0, y1)/self.scale_factor)
            
            # Extract image from the highlighted area
            pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor), clip=rect)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            try:
                # Convert to LaTeX
                latex = self.latex_ocr(img)
                
                if latex:
                    self.highlighted_text = f"${latex}$"
                    self.copy_to_clipboard(self.highlighted_text)
                    messagebox.showinfo("Highlight", "LaTeX expression copied to clipboard!")
                else:
                    # If LaTeX conversion fails, fall back to text extraction
                    words = page.get_text("words", clip=rect)
                    self.highlighted_text = " ".join(w[4] for w in words)
                    self.copy_to_clipboard(self.highlighted_text)
                    messagebox.showinfo("Highlight", "Text copied to clipboard!")
            except Exception as e:
                print(f"Error in LaTeX conversion: {str(e)}")
                # Fall back to text extraction
                words = page.get_text("words", clip=rect)
                self.highlighted_text = " ".join(w[4] for w in words)
                self.copy_to_clipboard(self.highlighted_text)
                messagebox.showinfo("Highlight", "Error in LaTeX conversion. Copied as text.")

            self.highlight_start = None
            if self.highlight_rectangle:
                self.pdf_canvas.delete(self.highlight_rectangle)
                self.highlight_rectangle = None

        if self.highlighted_text:
            self.submit_highlight_button.config(state=tk.NORMAL)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Necessary to finalize the clipboard operation
        pyperclip.copy(text)  # As a fallback, also use pyperclip
        print(f"Copied to clipboard: {text}")  # Debug print



    def submit_highlighted_text(self):
        """
        Submits the highlighted text to the AI for analysis.

        This method is called when the user clicks the "Submit Highlighted Text"
        button. It adds the highlighted text to the AI queue for analysis.
        """
        # Submit highlighted text to AI for analysis
        if self.highlighted_text:
            self.ai_queue.put(("highlight", self.highlighted_text))
            self.highlighted_text = ""
            self.submit_highlight_button.config(state=tk.DISABLED)

    def submit_pdf_to_ai(self):
        """
        Submits the entire PDF content to the AI for analysis.

        This method extracts text from the current page and the last two pages (if available)
        of the PDF and submits it to the AI for analysis. It uses OCR for scanned or
        photographed pages.
        """
        if self.current_pdf:
            total_pages = len(self.current_pdf)
            pages_to_submit = []

            # Add the current page
            pages_to_submit.append(self.current_page)

            # Add the last two pages if they exist and are different from the current page
            if total_pages > 1:
                if self.current_page != total_pages - 1:
                    pages_to_submit.append(total_pages - 1)
                if total_pages > 2 and self.current_page != total_pages - 2:
                    pages_to_submit.append(total_pages - 2)

            # Remove duplicates and sort
            pages_to_submit = sorted(set(pages_to_submit))

            full_text = ""
            for page_num in pages_to_submit:
                page = self.current_pdf[page_num]
                
                # Try to get text using PyMuPDF
                page_text = page.get_text()
                
                # If no text is extracted, use OCR
                if not page_text.strip():
                    # Convert page to image
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Perform OCR
                    page_text = pytesseract.image_to_string(img)
                
                full_text += f"Page {page_num + 1}:\n{page_text}\n\n"

            # Truncate the text if it's too long
            max_chars = 8000  # Adjust this value as needed
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + "... [truncated]"

            self.ai_queue.put(("pdf", full_text))
            messagebox.showinfo("PDF Submitted", "The content of the current page and the last two pages (if available) has been submitted to the AI for analysis.")
        else:
            messagebox.showerror("Error", "No PDF is currently loaded.")


    def send_message(self):
        """
        Sends a user message to the AI.

        This method is called when the user clicks the "Send" button.
        It retrieves the user's message, adds it to the chat history,
        and submits it to the AI for analysis.
        """
        user_message = self.user_input.get()
        self.update_chat_history(f"You: {user_message}\n")
        
        if user_message.startswith("/chat "):
            query = user_message[6:]  # Remove "/chat " from the beginning
            try:
                response = self.ddgs.chat(query, model=self.chat_model)
                self.update_chat_history(f"DuckDuckGo AI: {response}\n")
            except Exception as e:
                error_message = f"Error in DuckDuckGo chat: {str(e)}"
                self.update_chat_history(f"Error: {error_message}\n")


        elif user_message.startswith("/search "):
            query = user_message[8:]  # Remove "/search " from the beginning
            search_results = self.perform_web_search(query)
            result_text = "Search Results:\n"
            for result in search_results:
                result_text += f"- {result['title']}: {result['href']}\n"
            self.update_chat_history(result_text)
            self.ai_queue.put(("search", result_text))
        else:
            self.ai_queue.put(("message", user_message))
        
        self.user_input.delete(0, tk.END)


    def update_chat_history(self, message):
        """
        Updates the chat history with new messages.

        This method is called when a new message is received from the AI
        or when the user sends a message. It appends the message to the
        chat history and scrolls to the bottom.

        Parameters:
        - message (str): The message to append to the chat history
        """
        # Update chat history with new messages
        self.chat_history.config(state='normal')
    
        # Split the message into parts
        parts = message.split('$$')
        
        for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Regular text
                    self.chat_history.insert(tk.END, part)
                else:
                    # LaTeX content
                    latex_image = render_latex(part)
                    self.chat_history.image_create(tk.END, image=latex_image)
                    # Keep a reference to prevent garbage collection
                    self.chat_history.images.append(latex_image)
        
        self.chat_history.insert(tk.END, '\n')
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

    def toggle_ai_panel(self):
        """
        Toggles the visibility of the AI chat panel.

        This method is called when the user clicks the "Toggle AI" button.
        It hides or shows the AI chat panel and updates the button text
        accordingly.
        """
        if self.right_panel.winfo_viewable():
            self.paned_window.forget(self.right_panel)
            self.toggle_ai_button.config(text="Show AI")
        else:
            self.paned_window.add(self.right_panel)  # Remove the weight parameter
            self.toggle_ai_button.config(text="Hide AI")
        self.paned_window.update()

    def prev_page(self):
        """
        Goes to the previous page of the PDF.

        This method is called when the user clicks the "Previous Page" button.
        It decreases the current page number and displays the new page.
        """
        # Go to previous page of PDF
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        """
        Goes to the next page of the PDF.

        This method is called when the user clicks the "Next Page" button.
        It increases the current page number and displays the new page.
        """
        # Go to next page of PDF
        if self.current_pdf and self.current_page < len(self.current_pdf) - 1:
            self.current_page += 1
            self.display_page()

    def on_mousewheel(self, event):
        """
        Handles mouse wheel scrolling on the PDF canvas.

        This method is called when the user scrolls the mouse wheel over the PDF canvas.
        It adjusts the view of the canvas based on the scroll direction.

        Parameters:
        - event (tk.Event): The mouse wheel event
        """
        # Determine the scroll direction and amount
        if event.delta:
            scroll_direction = -1 if event.delta > 0 else 1
        elif event.num == 4:
            scroll_direction = -1
        elif event.num == 5:
            scroll_direction = 1
        else:
            return

        # Scroll the canvas
        self.pdf_canvas.yview_scroll(scroll_direction, "units")

    def start_ai_thread(self):
        """
        Starts a separate thread for AI processing.

        This method creates and starts a daemon thread that runs the ai_worker
        function, allowing AI processing to occur in the background without
        blocking the main UI thread.
        """
        threading.Thread(target=self.ai_worker, daemon=True).start()

    def ai_worker(self):
        """
        Worker function for the AI processing thread.

        This function runs in a separate thread and continuously processes
        tasks from the AI queue. It handles different types of tasks (highlight,
        message, pdf) and updates the chat history with AI responses.
        """
        while True:
            # Get a task from the queue
            task_type, content = self.ai_queue.get()
            
            try:
                # Process the task based on its type
                if task_type == "highlight":
                    self.messages.append({"role": "user", "content": f"Analyze this highlighted text: {content}"})
                elif task_type == "message":
                    self.messages.append({"role": "user", "content": content})
                elif task_type == "pdf":
                    self.messages.append({"role": "user", "content": f"Here's the full content of the PDF: {content[:9000]}... [truncated]"})
                elif task_type == "search":
                    self.messages.append({"role": "user", "content": f"Here are the search results: {content}"})
            
                # Get the AI's response
                response = completion(self.messages)
                self.messages.append({"role": "assistant", "content": response})
            
                # Check if the AI response contains a search command
                if "/search" in response:
                    search_query = response.split("/search", 1)[1].strip()
                    search_results = self.perform_web_search(search_query)
                    
                    if search_results:
                        result_text = "AI-initiated Search Results:\n"
                        for result in search_results:
                            if isinstance(result, dict) and 'title' in result and 'href' in result:
                                result_text += f"- {result['title']}: {result['href']}\n"
                            else:
                                result_text += f"- {str(result)}\n"
                        self.root.after(0, self.update_chat_history, result_text)
                        self.messages.append({"role": "user", "content": result_text})
                        response += f"\n\nI've performed a search for '{search_query}'. Here are the results:\n{result_text}"
                    else:
                        no_results_message = f"No results found for the search query: '{search_query}'"
                        self.root.after(0, self.update_chat_history, no_results_message)
                        self.messages.append({"role": "user", "content": no_results_message})
                        response += f"\n\n{no_results_message}"
            
                # Update the chat history in the main thread
                self.root.after(0, self.update_chat_history, f"AI: {response}\n")
            
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
                self.root.after(0, self.update_chat_history, f"AI: {error_message}\n")
            
            # Mark the task as done
            self.ai_queue.task_done()


    def perform_web_search(self, query, max_results=5):
        #Performs a web search using DuckDuckGo and returns the results.
        
        """Args:
            query (str): The search query.
            max_results (int): Maximum number of results to return.
        
        Returns:
            list: A list of dictionaries containing search results.
       """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return [{"title": "No results found", "href": ""}]
            
            return results
        except Exception as e:
            print(f"Error performing web search: {str(e)}")
            return [{"title": f"Error performing web search: {str(e)}", "href": ""}]
    
    def convert_to_latex(self, text):
        """
        Attempts to convert text to LaTeX using pix2tex.

        Parameters:
        - text (str): The text to convert

        Returns:
        - str or None: The LaTeX string if conversion was successful, None otherwise
        """
        try:
            latex = self.latex_ocr(text)
            if latex and latex != text:  # If conversion successful and different from input
                return latex
        except Exception as e:
            print(f"Error converting text to LaTeX: {str(e)}")
        return None

    def convert_image_to_latex(self, image):
        """
        Attempts to convert an image to LaTeX using pix2tex.

        Parameters:
        - image (PIL.Image): The image to convert

        Returns:
        - str or None: The LaTeX string if conversion was successful, None otherwise
        """
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            return self.latex_ocr(img_byte_arr)
        except Exception as e:
            print(f"Error converting image to LaTeX: {str(e)}")
            return None



def render_latex(latex_string, fontsize=12, dpi=100):
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(6, 0.5), dpi=dpi)
        ax.axis('off')
        
        # Render the LaTeX string
        ax.text(0, 0.5, f'${latex_string}$', fontsize=fontsize, va='center')
        
        # Save the figure to a buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        
        # Create a PhotoImage from the buffer
        img = Image.open(buf)
        return ImageTk.PhotoImage(img)

def main():

    """ Main function to run the PDFStudyAssistant application.
    This function creates the root window and initializes the PDFStudyAssistant
    application, then starts the main event loop."""
    root = tkdnd.TkinterDnD.Tk()
    app = PDFStudyAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()