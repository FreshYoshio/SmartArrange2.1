import os
import shutil
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext
from datetime import datetime, timedelta
import webbrowser
import sqlite3
import numpy as np
import time
from PIL import Image, ImageTk, ImageOps, ImageFilter
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import pyautogui
import pygame
from gtts import gTTS
import tempfile
import json
from difflib import SequenceMatcher
import warnings
import re
from collections import defaultdict
import heapq
warnings.filterwarnings('ignore')

# ========== CONSTANTS AND CONFIGURATIONS ==========
EXTENSION_FOLDERS = {
    # Documents
    '.pdf': 'PDFs', '.doc': 'Word', '.docx': 'Word', '.txt': 'Text', 
    '.rtf': 'Text', '.odt': 'OpenOffice', '.xls': 'Excel', '.xlsx': 'Excel',
    '.ppt': 'PowerPoint', '.pptx': 'PowerPoint', '.csv': 'Data',
    
    # Images
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images',
    '.bmp': 'Images', '.svg': 'Vector', '.webp': 'Images', '.tiff': 'Images',
    '.psd': 'Photoshop', '.ai': 'Illustrator',
    
    # Videos
    '.mp4': 'Videos', '.mov': 'Videos', '.avi': 'Videos', '.mkv': 'Videos',
    '.flv': 'Videos', '.wmv': 'Videos', '.mpeg': 'Videos', '.webm': 'Videos',
    
    # Audio
    '.mp3': 'Audio', '.wav': 'Audio', '.ogg': 'Audio', '.m4a': 'Audio',
    '.flac': 'Audio', '.aac': 'Audio', '.wma': 'Audio',
    
    # Archives
    '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives',
    '.gz': 'Archives', '.bz2': 'Archives', '.iso': 'Disk Images',
    
    # Programs
    '.exe': 'Executables', '.msi': 'Installers', '.dmg': 'Mac Installers',
    '.pkg': 'Mac Installers', '.deb': 'Linux Packages', '.rpm': 'Linux Packages',
    
    # Code
    '.py': 'Python', '.js': 'JavaScript', '.html': 'Web', '.css': 'Web',
    '.php': 'PHP', '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.h': 'Headers',
    '.json': 'JSON', '.xml': 'XML', '.sql': 'SQL', '.sh': 'Shell Scripts'
}

THEMES = {
    'Dark': {
        'bg': '#1e1e1e',
        'fg': '#e0e0e0',
        'accent': '#3a3a3a',
        'highlight': '#2d2d2d',
        'text': '#ffffff',
        'button': '#4e5254'
    },
    'Light': {
        'bg': '#f5f5f5',
        'fg': '#333333',
        'accent': '#e0e0e0',
        'highlight': '#ffffff',
        'text': '#000000',
        'button': '#d0d0d0'
    },
    'Ocean': {
        'bg': '#0f2d44',
        'fg': '#c0e0ff',
        'accent': '#1a4b6e',
        'highlight': '#153d57',
        'text': '#e0f7ff',
        'button': '#00688b'
    },
    'Professional': {
        'bg': '#2c3e50',
        'fg': '#ecf0f1',
        'accent': '#34495e',
        'highlight': '#3d566e',
        'text': '#ffffff',
        'button': '#3498db'
    }
}

# ========== HELPER CLASSES ==========
class FileAnalyzer:
    @staticmethod
    def get_similar_files(target_file, folder_path, threshold=0.7):
        """Find similar files based on content or name"""
        try:
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            if not files:
                return []
            
            # Compare filenames
            similar = []
            target_name = os.path.basename(target_file)
            for f in files:
                ratio = SequenceMatcher(None, target_name, f).ratio()
                if ratio > threshold and f != target_name:
                    similar.append(f)
            
            # Compare content for text files
            if target_file.endswith(('.txt', '.pdf', '.docx')):
                try:
                    contents = []
                    valid_files = [target_file]
                    
                    for f in files:
                        if f.endswith(('.txt', '.pdf', '.docx')):
                            valid_files.append(os.path.join(folder_path, f))
                    
                    vectorizer = TfidfVectorizer()
                    for f in valid_files:
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            contents.append(file.read())
                    
                    tfidf = vectorizer.fit_transform(contents)
                    similarities = cosine_similarity(tfidf[0:1], tfidf)[0]
                    
                    for i, sim in enumerate(similarities[1:], 1):
                        if sim > threshold:
                            similar.append(os.path.basename(valid_files[i]))
                except Exception:
                    pass
            
            return list(set(similar))
        except Exception:
            return []

class StoragePredictor:
    def __init__(self):
        self.history = defaultdict(list)
        
    def add_record(self, path, size):
        """Add storage usage record"""
        timestamp = datetime.now()
        self.history[path].append((timestamp, size))
        
    def predict_usage(self, path, days=90):
        """Predict future storage usage"""
        if path not in self.history or len(self.history[path]) < 2:
            return None
            
        records = self.history[path]
        x = [(r[0] - records[0][0]).days for r in records]
        y = [r[1] for r in records]
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi**2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        intercept = (sum_y - slope * sum_x) / n
        
        future_day = (datetime.now() - records[0][0]).days + days
        predicted = slope * future_day + intercept
        
        return max(0, predicted)

# ========== MAIN APPLICATION ==========
class ModernFileManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modern File Manager")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Initialize components
        self.settings = {
            'language': 'EN',
            'theme': 'Professional',
            'ai_enabled': True,
            'auto_clean': False,
            'notifications': True,
            'dark_mode': True
        }
        
        self.current_folder = ""
        self.selected_files = []
        self.file_tags = {}
        self.file_history = {}
        self.storage_predictor = StoragePredictor()
        self.pygame_initialized = False
        
        # Load data
        self.load_config()
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """Setup the modern UI"""
        self.configure(bg=THEMES[self.settings['theme']]['bg'])
        
        # Main container with modern styling
        self.main_container = ttk.Frame(self, style='Main.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header with gradient
        self.create_header()
        
        # Main content with sidebar
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
        
        # Initialize pygame for audio
        self.init_audio()
        
    def create_header(self):
        """Create modern header with gradient"""
        header = tk.Frame(self.main_container, bg=THEMES[self.settings['theme']]['accent'], 
                         height=60, relief=tk.FLAT, bd=0)
        header.pack(fill=tk.X, pady=0)
        
        # Logo and title with modern font
        logo_frame = tk.Frame(header, bg=THEMES[self.settings['theme']]['accent'])
        logo_frame.pack(side=tk.LEFT, padx=20)
        
        logo = tk.Label(logo_frame, text="📁", font=('Segoe UI', 24), 
                       bg=THEMES[self.settings['theme']]['accent'], 
                       fg=THEMES[self.settings['theme']]['text'])
        logo.pack(side=tk.LEFT, padx=5)
        
        title = tk.Label(logo_frame, text="Modern File Manager", 
                        font=('Segoe UI', 16, 'bold'), 
                        bg=THEMES[self.settings['theme']]['accent'], 
                        fg=THEMES[self.settings['theme']]['text'])
        title.pack(side=tk.LEFT)
        
        # Navigation buttons with modern icons
        nav_frame = tk.Frame(header, bg=THEMES[self.settings['theme']]['accent'])
        nav_frame.pack(side=tk.RIGHT, padx=20)
        
        nav_buttons = [
            ("🏠", self.go_home, "Home"),
            ("⬆️", self.go_up, "Up"),
            ("🔍", self.show_search, "Search"),
            ("⚙️", self.open_settings_dialog, "Settings"),
            ("❓", self.show_help, "Help")
        ]
        
        for icon, cmd, tooltip in nav_buttons:
            btn = tk.Button(nav_frame, text=icon, font=('Segoe UI', 14), 
                           command=cmd, relief=tk.FLAT, bd=0,
                           bg=THEMES[self.settings['theme']]['accent'], 
                           fg=THEMES[self.settings['theme']]['text'],
                           activebackground=THEMES[self.settings['theme']]['highlight'])
            btn.pack(side=tk.LEFT, padx=5)
            self.create_tooltip(btn, tooltip)
    
    def create_main_content(self):
        """Create main content area with sidebar"""
        content = ttk.Frame(self.main_container)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar - Quick access and tools
        sidebar = ttk.Frame(content, width=250, style='Sidebar.TFrame')
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        self.create_sidebar(sidebar)
        
        # Right content area - File browser and preview
        main_area = ttk.Frame(content, style='MainArea.TFrame')
        main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_file_browser(main_area)
        self.create_preview_panel(main_area)
    
    def create_sidebar(self, parent):
        """Create sidebar with quick access and tools"""
        # Quick access section
        quick_frame = ttk.LabelFrame(parent, text="Quick Access", padding=10)
        quick_frame.pack(fill=tk.X, pady=(10, 5), padx=5)
        
        quick_folders = [
            ("Documents", "📄", os.path.expanduser("~/Documents")),
            ("Desktop", "🖥️", os.path.expanduser("~/Desktop")),
            ("Downloads", "📥", os.path.expanduser("~/Downloads")),
            ("Pictures", "🖼️", os.path.expanduser("~/Pictures"))
        ]
        
        for name, icon, path in quick_folders:
            btn = ttk.Button(quick_frame, text=f"{icon} {name}", 
                            command=lambda p=path: self.set_folder(p),
                            style='Sidebar.TButton')
            btn.pack(fill=tk.X, pady=2)
        
        # Add folder selection button
        ttk.Button(quick_frame, text="📂 Select Folder", 
                  command=self.select_folder,
                  style='Sidebar.TButton').pack(fill=tk.X, pady=5)
        
        # Tools section
        tools_frame = ttk.LabelFrame(parent, text="Tools", padding=10)
        tools_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tools = [
            ("Organize Files", "🗂️", self.start_organizing),
            ("Find Duplicates", "🔍", self.find_duplicates),
            ("Clean Unused", "🧹", self.clean_unused_files),
            ("Bulk Rename", "✏️", self.bulk_rename_files),
            ("Storage Stats", "📊", self.show_storage_stats)
        ]
        
        for text, icon, cmd in tools:
            btn = ttk.Button(tools_frame, text=f"{icon} {text}", 
                            command=cmd, style='Sidebar.TButton')
            btn.pack(fill=tk.X, pady=2)
        
        # Tags section
        tags_frame = ttk.LabelFrame(parent, text="Tags", padding=10)
        tags_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.tag_entry = ttk.Entry(tags_frame)
        self.tag_entry.pack(fill=tk.X, pady=2)
        
        ttk.Button(tags_frame, text="Add Tag", command=self.add_tag_to_selected,
                  style='Sidebar.TButton').pack(fill=tk.X, pady=2)
        
        # Current folder info
        info_frame = ttk.LabelFrame(parent, text="Folder Info", padding=10)
        info_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.folder_info = ttk.Label(info_frame, text="No folder selected")
        self.folder_info.pack(fill=tk.X)
        
        self.folder_stats = ttk.Label(info_frame, text="")
        self.folder_stats.pack(fill=tk.X)
    
    def create_file_browser(self, parent):
        """Create the main file browser area"""
        browser_frame = ttk.Frame(parent)
        browser_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search and filter bar
        search_frame = ttk.Frame(browser_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.on_search)
        
        ttk.Button(search_frame, text="Search", command=self.filter_files,
                  style='Accent.TButton').pack(side=tk.LEFT)
        
        # File list with modern styling
        self.file_list = ttk.Treeview(browser_frame, columns=('name', 'size', 'type', 'modified', 'tags'), 
                                     selectmode='extended', style='Treeview')
        self.file_list.heading('#0', text='')
        self.file_list.heading('name', text='File Name')
        self.file_list.heading('size', text='Size')
        self.file_list.heading('type', text='Type')
        self.file_list.heading('modified', text='Modified')
        self.file_list.heading('tags', text='Tags')
        
        self.file_list.column('#0', width=0, stretch=tk.NO)
        self.file_list.column('name', width=300)
        self.file_list.column('size', width=80, anchor=tk.E)
        self.file_list.column('type', width=100)
        self.file_list.column('modified', width=120)
        self.file_list.column('tags', width=150)
        
        scroll_y = ttk.Scrollbar(browser_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.configure(yscrollcommand=scroll_y.set)
        
        scroll_x = ttk.Scrollbar(browser_frame, orient=tk.HORIZONTAL, command=self.file_list.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list.configure(xscrollcommand=scroll_x.set)
        
        self.file_list.pack(fill=tk.BOTH, expand=True)
        self.file_list.bind('<<TreeviewSelect>>', self.on_file_select)
        
        # Context menu
        self.create_context_menu()
    
    def create_preview_panel(self, parent):
        """Create the file preview panel"""
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, pady=(0, 10), padx=10)
        
        # Tabbed interface for different preview types
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Image preview tab
        self.image_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.image_tab, text="Image")
        self.image_preview = ttk.Label(self.image_tab)
        self.image_preview.pack(fill=tk.BOTH, expand=True)
        
        # Text preview tab
        self.text_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.text_tab, text="Text")
        self.text_preview = scrolledtext.ScrolledText(self.text_tab, wrap=tk.WORD)
        self.text_preview.pack(fill=tk.BOTH, expand=True)
        
        # Details tab
        self.details_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.details_tab, text="Details")
        
        details_frame = ttk.Frame(self.details_tab)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.file_name = ttk.Label(details_frame, text="")
        self.file_name.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.file_size = ttk.Label(details_frame, text="")
        self.file_size.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Type:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.file_type = ttk.Label(details_frame, text="")
        self.file_type.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Modified:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.file_modified = ttk.Label(details_frame, text="")
        self.file_modified.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Created:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.file_created = ttk.Label(details_frame, text="")
        self.file_created.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Media controls for audio/video
        self.media_controls = ttk.Frame(details_frame)
        self.media_controls.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.play_button = ttk.Button(self.media_controls, text="▶", width=3, 
                                    command=self.play_media, style='Accent.TButton')
        self.play_button.pack(side=tk.LEFT, padx=2)
        self.stop_button = ttk.Button(self.media_controls, text="⏹", width=3, 
                                    command=self.stop_media, style='Accent.TButton')
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Notes section
        notes_frame = ttk.LabelFrame(details_frame, text="Notes", padding=5)
        notes_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.notes_text = scrolledtext.ScrolledText(notes_frame, height=4, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.bind("<FocusOut>", self.save_file_note)
        
        ttk.Button(notes_frame, text="Save Note", command=self.save_file_note,
                  style='Accent.TButton').pack(fill=tk.X, pady=5)
    
    def create_status_bar(self):
        """Create modern status bar"""
        status = ttk.Frame(self.main_container, style='Status.TFrame')
        status.pack(fill=tk.X, pady=(0, 0))
        
        self.status_text = tk.StringVar(value="Ready")
        status_label = ttk.Label(status, textvariable=self.status_text, 
                                style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Current path display
        self.path_display = ttk.Label(status, text="", style='Status.TLabel')
        self.path_display.pack(side=tk.RIGHT, padx=10)
    
    def create_context_menu(self):
        """Create right-click context menu with modern styling"""
        self.context_menu = tk.Menu(self, tearoff=0, bg=THEMES[self.settings['theme']]['highlight'], 
                                  fg=THEMES[self.settings['theme']]['text'],
                                  activebackground=THEMES[self.settings['theme']]['accent'],
                                  activeforeground=THEMES[self.settings['theme']]['text'])
        
        actions = [
            ("Open", self.open_file),
            ("Open With...", self.open_with),
            ("Rename", self.rename_file),
            ("Delete", self.delete_file),
            ("Copy Path", self.copy_path),
            ("Show in Explorer", self.show_in_explorer),
            ("Properties", self.show_properties)
        ]
        
        for text, cmd in actions:
            self.context_menu.add_command(label=text, command=cmd)
        
        self.file_list.bind("<Button-3>", self.show_context_menu)
    
    def create_tooltip(self, widget, text):
        """Create a modern tooltip for widgets"""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_withdraw()
        
        label = tk.Label(tooltip, text=text, bg="#ffffe0", relief=tk.SOLID, 
                        borderwidth=1, padx=4, pady=2)
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty() + (widget.winfo_height() - label.winfo_reqheight()) // 2
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.wm_deiconify()
        
        def leave(event):
            tooltip.wm_withdraw()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    # ========== THEME AND STYLING ==========
    def apply_theme(self):
        """Apply the current theme settings"""
        theme = THEMES[self.settings['theme']]
        
        self.configure(bg=theme['bg'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure main styles
        style.configure('.', 
                      background=theme['bg'], 
                      foreground=theme['fg'],
                      font=('Segoe UI', 10))
        
        # Frame styles
        style.configure('Main.TFrame', background=theme['bg'])
        style.configure('Sidebar.TFrame', background=theme['accent'])
        style.configure('Status.TFrame', background=theme['accent'])
        style.configure('MainArea.TFrame', background=theme['bg'])
        
        # Label styles
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('Status.TLabel', background=theme['accent'], foreground=theme['text'])
        
        # Button styles
        style.configure('TButton', 
                       background=theme['button'], 
                       foreground=theme['text'],
                       borderwidth=1,
                       relief=tk.FLAT,
                       padding=6,
                       font=('Segoe UI', 9))
        
        style.configure('Accent.TButton', 
                       background='#4CAF50', 
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'))
        
        style.configure('Sidebar.TButton', 
                       background=theme['accent'], 
                       foreground=theme['text'],
                       anchor=tk.W,
                       padding=6)
        
        style.map('TButton',
                 background=[('active', theme['highlight']), ('!disabled', theme['button'])],
                 foreground=[('active', theme['fg']), ('!disabled', theme['fg'])])
        
        style.map('Sidebar.TButton',
                 background=[('active', theme['highlight']), ('!disabled', theme['accent'])],
                 foreground=[('active', theme['fg']), ('!disabled', theme['fg'])])
        
        # Treeview styles
        style.configure('Treeview', 
                      background=theme['highlight'],
                      foreground=theme['fg'],
                      fieldbackground=theme['highlight'],
                      borderwidth=0)
        
        style.configure('Treeview.Heading', 
                      background=theme['accent'],
                      foreground=theme['text'],
                      relief=tk.FLAT,
                      font=('Segoe UI', 9, 'bold'))
        
        style.map('Treeview',
                background=[('selected', '#347083')],
                foreground=[('selected', 'white')])
        
        # Notebook styles
        style.configure('TNotebook', background=theme['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                      background=theme['accent'],
                      foreground=theme['text'],
                      padding=[10, 5],
                      font=('Segoe UI', 9))
        
        style.map('TNotebook.Tab',
                background=[('selected', theme['bg']),
                            ('active', theme['highlight'])],
                foreground=[('selected', theme['fg']),
                           ('active', theme['fg'])])
        
        # Scrollbar styles
        style.configure('Vertical.TScrollbar', 
                      background=theme['accent'],
                      troughcolor=theme['bg'],
                      bordercolor=theme['bg'],
                      arrowcolor=theme['fg'],
                      gripcount=0,
                      relief=tk.FLAT)
        
        style.configure('Horizontal.TScrollbar', 
                      background=theme['accent'],
                      troughcolor=theme['bg'],
                      bordercolor=theme['bg'],
                      arrowcolor=theme['fg'],
                      gripcount=0,
                      relief=tk.FLAT)
        
        # Update all widgets
        self.update_all_widgets()
    
    def update_all_widgets(self):
        """Update all widgets to match current theme"""
        theme = THEMES[self.settings['theme']]
        
        # Update main window
        self.configure(bg=theme['bg'])
        
        # Update all child widgets
        for widget in self.winfo_children():
            self.update_widget_colors(widget, theme)
    
    def update_widget_colors(self, widget, theme):
        """Recursively update widget colors"""
        try:
            if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Listbox)):
                widget.config(bg=theme['bg'], fg=theme['fg'])
                
                if isinstance(widget, tk.Button):
                    widget.config(activebackground=theme['highlight'],
                                activeforeground=theme['fg'])
        except:
            pass
        
        for child in widget.winfo_children():
            self.update_widget_colors(child, theme)
    
    # ========== FILE OPERATIONS ==========
    def set_folder(self, path):
        """Set the current working folder"""
        if os.path.isdir(path):
            self.current_folder = path
            self.update_file_list()
            self.update_storage_stats()
            self.update_folder_info()
            self.path_display.config(text=path)
    
    def select_folder(self):
        """Open dialog to select a folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.set_folder(folder)
    
    def go_home(self):
        """Navigate to home directory"""
        self.set_folder(os.path.expanduser("~"))
    
    def go_up(self):
        """Navigate up one directory level"""
        if self.current_folder and os.path.dirname(self.current_folder) != self.current_folder:
            self.set_folder(os.path.dirname(self.current_folder))
    
    def update_file_list(self):
        """Update the file list view"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            return
        
        self.file_list.delete(*self.file_list.get_children())
        
        try:
            files = 0
            folders = 0
            total_size = 0
            
            # Add ".." for parent directory
            if os.path.dirname(path) != path:
                self.file_list.insert('', tk.END, 
                                    values=("..", "", "Parent Directory", "", ""))
            
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    total_size += size
                    date = datetime.fromtimestamp(os.path.getmtime(item_path))
                    created = datetime.fromtimestamp(os.path.getctime(item_path))
                    ext = os.path.splitext(item)[1].lower()
                    tags = self.file_tags.get(item, "")
                    
                    self.file_list.insert('', tk.END, 
                                        values=(item, self.format_size(size), 
                                                EXTENSION_FOLDERS.get(ext, 'Other'), 
                                                date.strftime('%d.%m.%Y %H:%M'),
                                                tags))
                    files += 1
                else:
                    self.file_list.insert('', tk.END, 
                                       values=(item, "", "Folder", "", ""))
                    folders += 1
            
            self.update_folder_info(files, folders)
            self.status_text.set("Ready")
            
            # Record storage usage for prediction
            self.storage_predictor.add_record(path, total_size)
        except Exception as e:
            self.status_text.set(f"Error: {str(e)}")
    
    def update_folder_info(self, files=0, folders=0):
        """Update folder information display"""
        path = self.current_folder
        if not path:
            self.folder_info.config(text="No folder selected")
            self.folder_stats.config(text="")
            return
        
        try:
            stat = os.statvfs(path)
            total_space = stat.f_blocks * stat.f_frsize
            used_space = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
            free_space = stat.f_bavail * stat.f_frsize
            
            self.folder_info.config(text=f"Folder: {os.path.basename(path)}")
            self.folder_stats.config(text=f"Files: {files} | Folders: {folders}\n"
                                        f"Used: {self.format_size(used_space)} / "
                                        f"Free: {self.format_size(free_space)}")
        except:
            self.folder_info.config(text=f"Folder: {os.path.basename(path)}")
            self.folder_stats.config(text=f"Files: {files} | Folders: {folders}")
    
    def start_organizing(self):
        """Start organizing files into categorized folders"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Warning", "Please select a valid folder")
            return
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    folder_name = EXTENSION_FOLDERS.get(ext, 'Other')
                    target_dir = os.path.join(path, folder_name)
                    
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(item_path, os.path.join(target_dir, item))
            
            messagebox.showinfo("Success", "Files organized successfully!")
            self.update_file_list()
            self.update_storage_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Error while organizing:\n{str(e)}")
    
    def find_duplicates(self):
        """Find duplicate files in current folder"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Warning", "Please select a valid folder")
            return
        
        # Group files by size first (quick check)
        size_groups = defaultdict(list)
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                size_groups[size].append(item_path)
        
        # Then check hash for files with same size
        duplicates = []
        for size, files in size_groups.items():
            if len(files) > 1:
                hash_groups = defaultdict(list)
                for file in files:
                    with open(file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    hash_groups[file_hash].append(file)
                
                for hash, same_files in hash_groups.items():
                    if len(same_files) > 1:
                        duplicates.append(same_files)
        
        if not duplicates:
            messagebox.showinfo("Info", "No duplicate files found")
            return
        
        # Show duplicates in a new window
        dialog = tk.Toplevel(self)
        dialog.title("Duplicate Files")
        dialog.geometry("600x400")
        
        tree = ttk.Treeview(dialog, columns=('file', 'size'), selectmode='browse')
        tree.heading('#0', text='Group')
        tree.heading('file', text='File')
        tree.heading('size', text='Size')
        
        tree.column('#0', width=50, stretch=tk.NO)
        tree.column('file', width=400)
        tree.column('size', width=100)
        
        scroll_y = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scroll_y.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        for i, group in enumerate(duplicates, 1):
            for file in group:
                size = os.path.getsize(file)
                tree.insert('', tk.END, values=(file, self.format_size(size)), text=str(i))
        
        def delete_selected():
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                file = item['values'][0]
                if messagebox.askyesno("Confirm", f"Delete '{os.path.basename(file)}'?"):
                    try:
                        os.remove(file)
                        tree.delete(selected[0])
                    except Exception as e:
                        messagebox.showerror("Error", f"Delete failed:\n{str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Delete Selected", command=delete_selected,
                  style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def clean_unused_files(self):
        """Clean unused files (not accessed in 1 year)"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Warning", "Please select a valid folder")
            return
        
        threshold_date = datetime.now() - timedelta(days=365)
        unused_files = []
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                last_accessed = datetime.fromtimestamp(os.path.getatime(item_path))
                if last_accessed < threshold_date:
                    unused_files.append((item, last_accessed.strftime('%Y-%m-%d')))
        
        if not unused_files:
            messagebox.showinfo("Info", "No unused files found (not accessed in 1 year)")
            return
        
        # Show unused files in a new window
        dialog = tk.Toplevel(self)
        dialog.title("Unused Files")
        dialog.geometry("600x400")
        
        tree = ttk.Treeview(dialog, columns=('file', 'last_accessed'), selectmode='browse')
        tree.heading('#0', text='')
        tree.heading('file', text='File')
        tree.heading('last_accessed', text='Last Accessed')
        
        tree.column('#0', width=0, stretch=tk.NO)
        tree.column('file', width=400)
        tree.column('last_accessed', width=150)
        
        scroll_y = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scroll_y.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        for file, date in unused_files:
            tree.insert('', tk.END, values=(file, date))
        
        def delete_selected():
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                file = item['values'][0]
                filepath = os.path.join(path, file)
                if messagebox.askyesno("Confirm", f"Delete '{file}'?"):
                    try:
                        os.remove(filepath)
                        tree.delete(selected[0])
                    except Exception as e:
                        messagebox.showerror("Error", f"Delete failed:\n{str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Delete Selected", command=delete_selected,
                  style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def bulk_rename_files(self):
        """Bulk rename files with pattern"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Warning", "Please select a valid folder")
            return
        
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if not files:
            messagebox.showwarning("Warning", "No files found in selected folder")
            return
        
        # Create dialog for bulk rename
        dialog = tk.Toplevel(self)
        dialog.title("Bulk Rename")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Pattern:").pack(pady=5)
        
        pattern_var = tk.StringVar(value="file_{num:03d}{ext}")
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=40)
        pattern_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Preview:").pack(pady=5)
        
        preview_text = scrolledtext.ScrolledText(dialog, height=10, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def update_preview():
            preview_text.delete(1.0, tk.END)
            pattern = pattern_var.get()
            
            for i, file in enumerate(files[:10], 1):  # Show first 10 for preview
                name, ext = os.path.splitext(file)
                try:
                    new_name = pattern.format(num=i, name=name, ext=ext)
                    preview_text.insert(tk.END, f"{file} → {new_name}\n")
                except:
                    preview_text.insert(tk.END, f"Error with pattern for {file}\n")
        
        def apply_rename():
            pattern = pattern_var.get()
            confirm = messagebox.askyesno("Confirm", f"Rename {len(files)} files?")
            
            if confirm:
                try:
                    for i, file in enumerate(files, 1):
                        old_path = os.path.join(path, file)
                        name, ext = os.path.splitext(file)
                        new_name = pattern.format(num=i, name=name, ext=ext)
                        new_path = os.path.join(path, new_name)
                        
                        os.rename(old_path, new_path)
                    
                    messagebox.showinfo("Success", "Files renamed successfully!")
                    dialog.destroy()
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Error while renaming:\n{str(e)}")
        
        pattern_var.trace_add('write', lambda *args: update_preview())
        update_preview()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Apply", command=apply_rename,
                  style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def show_storage_stats(self):
        """Show detailed storage statistics"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Warning", "Please select a valid folder")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Storage Statistics")
        dialog.geometry("800x600")
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # File type distribution
        type_frame = ttk.Frame(notebook)
        notebook.add(type_frame, text="File Types")
        
        fig1 = plt.Figure(figsize=(6, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        
        file_types = defaultdict(int)
        for item in os.listdir(path):
            if os.path.isfile(os.path.join(path, item)):
                ext = os.path.splitext(item)[1].lower()
                file_types[EXTENSION_FOLDERS.get(ext, 'Other')] += 1
        
        if file_types:
            ax1.pie(file_types.values(), labels=file_types.keys(), autopct='%1.1f%%')
            ax1.set_title("File Type Distribution")
        else:
            ax1.text(0.5, 0.5, "No files found", ha='center', va='center')
        
        canvas1 = FigureCanvasTkAgg(fig1, master=type_frame)
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Size distribution
        size_frame = ttk.Frame(notebook)
        notebook.add(size_frame, text="Size Distribution")
        
        fig2 = plt.Figure(figsize=(6, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        
        sizes = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                sizes.append(os.path.getsize(item_path) / (1024 * 1024))  # in MB
        
        if sizes:
            ax2.hist(sizes, bins=20, edgecolor='black')
            ax2.set_xlabel("File Size (MB)")
            ax2.set_ylabel("Count")
            ax2.set_title("File Size Distribution")
        else:
            ax2.text(0.5, 0.5, "No files found", ha='center', va='center')
        
        canvas2 = FigureCanvasTkAgg(fig2, master=size_frame)
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Storage prediction
        pred_frame = ttk.Frame(notebook)
        notebook.add(pred_frame, text="Storage Prediction")
        
        fig3 = plt.Figure(figsize=(6, 4), dpi=100)
        ax3 = fig3.add_subplot(111)
        
        prediction = self.storage_predictor.predict_usage(path)
        if prediction and len(self.storage_predictor.history[path]) >= 2:
            records = self.storage_predictor.history[path]
            x = [(r[0] - records[0][0]).days for r in records]
            y = [r[1] / (1024 * 1024) for r in records]  # Convert to MB
            
            ax3.plot(x, y, 'bo-', label='History')
            ax3.plot([x[-1], 90], [y[-1], prediction / (1024 * 1024)], 'r--', label='Prediction')
            ax3.set_xlabel("Days")
            ax3.set_ylabel("Storage Usage (MB)")
            ax3.set_title("Storage Usage Prediction (Next 90 Days)")
            ax3.legend()
            ax3.grid(True)
        else:
            ax3.text(0.5, 0.5, "Not enough data for prediction", ha='center', va='center')
        
        canvas3 = FigureCanvasTkAgg(fig3, master=pred_frame)
        canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # ========== FILE PREVIEW AND SELECTION ==========
    def on_file_select(self, event):
        """Handle file selection"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            
            # Handle parent directory navigation
            if filename == "..":
                self.go_up()
                return
            
            filepath = os.path.join(self.current_folder, filename)
            
            # Update file details
            self.file_name.config(text=filename)
            
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                self.file_size.config(text=self.format_size(size))
                
                ext = os.path.splitext(filename)[1].lower()
                self.file_type.config(text=EXTENSION_FOLDERS.get(ext, 'Other'))
                
                modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                self.file_modified.config(text=modified.strftime('%Y-%m-%d %H:%M:%S'))
                
                created = datetime.fromtimestamp(os.path.getctime(filepath))
                self.file_created.config(text=created.strftime('%Y-%m-%d %H:%M:%S'))
                
                # Show appropriate preview
                self.show_file_preview(filepath)
                
                # Show media controls for audio/video
                if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.mp4', '.avi', '.mov')):
                    self.media_controls.grid()
                else:
                    self.media_controls.grid_remove()
            else:
                # Handle folder selection
                self.file_size.config(text="")
                self.file_type.config(text="Folder")
                self.file_modified.config(text="")
                self.file_created.config(text="")
                self.clear_previews()
                self.media_controls.grid_remove()
    
    def show_file_preview(self, filepath):
        """Show preview of the selected file"""
        filename = os.path.basename(filepath)
        
        # Clear all previews first
        self.clear_previews()
        
        # Show image preview
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            try:
                img = Image.open(filepath)
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                self.image_preview.config(image=photo)
                self.image_preview.image = photo  # Keep reference
                self.preview_notebook.select(self.image_tab)
            except Exception as e:
                self.text_preview.insert(tk.END, f"Could not load image: {str(e)}")
                self.preview_notebook.select(self.text_tab)
        
        # Show text preview for text files
        elif filename.lower().endswith(('.txt', '.log', '.csv', '.json', '.xml', '.py', '.js', '.html', '.css')):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_preview.insert(tk.END, content)
                self.preview_notebook.select(self.text_tab)
            except Exception as e:
                self.text_preview.insert(tk.END, f"Could not load file: {str(e)}")
                self.preview_notebook.select(self.text_tab)
        
        # Default to details tab
        else:
            self.preview_notebook.select(self.details_tab)
    
    def clear_previews(self):
        """Clear all preview panes"""
        self.image_preview.config(image=None)
        if hasattr(self.image_preview, 'image'):
            del self.image_preview.image
        self.text_preview.delete(1.0, tk.END)
    
    # ========== FILE OPERATIONS ==========
    def open_file(self):
        """Open selected file with default application"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            try:
                os.startfile(path)
                # Record file access
                self.file_history[filename] = datetime.now()
            except:
                messagebox.showerror("Error", "Could not open file!")
    
    def open_with(self):
        """Open selected file with specific application"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            # In a real implementation, this would show a file dialog to select an app
            messagebox.showinfo("Info", f"Would open {filename} with selected application")
    
    def rename_file(self):
        """Rename selected file"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            old_name = item['values'][0]
            old_path = os.path.join(self.current_folder, old_name)
            
            new_name = simpledialog.askstring("Rename", 
                                            "New name:", 
                                            initialvalue=old_name)
            if new_name and new_name != old_name:
                try:
                    new_path = os.path.join(self.current_folder, new_name)
                    os.rename(old_path, new_path)
                    
                    # Update tags and notes if they exist
                    if old_name in self.file_tags:
                        self.file_tags[new_name] = self.file_tags.pop(old_name)
                    
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Rename failed:\n{str(e)}")
    
    def delete_file(self):
        """Delete selected file"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            if messagebox.askyesno("Confirm", f"Delete '{filename}'?"):
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                    
                    # Remove from tags and history
                    if filename in self.file_tags:
                        del self.file_tags[filename]
                    if filename in self.file_history:
                        del self.file_history[filename]
                    
                    self.update_file_list()
                    self.update_storage_stats()
                except Exception as e:
                    messagebox.showerror("Error", f"Delete failed:\n{str(e)}")
    
    def copy_path(self):
        """Copy file path to clipboard"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            self.clipboard_clear()
            self.clipboard_append(path)
            self.status_text.set("Path copied to clipboard")
    
    def show_in_explorer(self):
        """Show file in system explorer"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(os.path.dirname(path))
                elif os.name == 'posix':  # macOS, Linux
                    os.system(f'open "{os.path.dirname(path)}"')
            except:
                messagebox.showerror("Error", "Could not open file explorer")
    
    def show_properties(self):
        """Show file properties"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            path = os.path.join(self.current_folder, filename)
            
            dialog = tk.Toplevel(self)
            dialog.title(f"Properties - {filename}")
            dialog.geometry("400x300")
            
            props = ttk.Frame(dialog)
            props.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(props, text=f"Name: {filename}").pack(anchor=tk.W)
            
            if os.path.isfile(path):
                size = os.path.getsize(path)
                ttk.Label(props, text=f"Size: {self.format_size(size)}").pack(anchor=tk.W)
                
                modified = datetime.fromtimestamp(os.path.getmtime(path))
                ttk.Label(props, text=f"Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}").pack(anchor=tk.W)
                
                created = datetime.fromtimestamp(os.path.getctime(path))
                ttk.Label(props, text=f"Created: {created.strftime('%Y-%m-%d %H:%M:%S')}").pack(anchor=tk.W)
                
                ext = os.path.splitext(filename)[1].lower()
                ttk.Label(props, text=f"Type: {EXTENSION_FOLDERS.get(ext, 'Unknown')}").pack(anchor=tk.W)
            else:
                ttk.Label(props, text="Type: Folder").pack(anchor=tk.W)
    
    def add_tag_to_selected(self):
        """Add tag to selected file"""
        selected = self.file_list.selection()
        if selected and self.tag_entry.get():
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            
            current_tags = self.file_tags.get(filename, "")
            new_tag = self.tag_entry.get()
            
            if current_tags:
                updated_tags = f"{current_tags}, {new_tag}"
            else:
                updated_tags = new_tag
            
            self.file_tags[filename] = updated_tags
            self.file_list.item(selected[0], values=(
                item['values'][0],
                item['values'][1],
                item['values'][2],
                item['values'][3],
                updated_tags
            ))
            self.tag_entry.delete(0, tk.END)
    
    # ========== SEARCH AND FILTER ==========
    def on_search(self, event=None):
        """Handle search box updates"""
        self.filter_files()
    
    def filter_files(self):
        """Filter files based on search query"""
        query = self.search_var.get().lower()
        path = self.current_folder
        
        if not path:
            return
        
        self.file_list.delete(*self.file_list.get_children())
        
        try:
            # Add parent directory link
            if os.path.dirname(path) != path:
                self.file_list.insert('', tk.END, 
                                    values=("..", "", "Parent Directory", "", ""))
            
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if not query or query in item.lower():
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        date = datetime.fromtimestamp(os.path.getmtime(item_path))
                        ext = os.path.splitext(item)[1].lower()
                        tags = self.file_tags.get(item, "")
                        
                        self.file_list.insert('', tk.END, 
                                            values=(item, self.format_size(size), 
                                                    EXTENSION_FOLDERS.get(ext, 'Other'), 
                                                    date.strftime('%d.%m.%Y %H:%M'),
                                                    tags))
                    else:
                        self.file_list.insert('', tk.END, 
                                           values=(item, "", "Folder", "", ""))
        except Exception as e:
            self.status_text.set(f"Error: {str(e)}")
    
    def show_search(self):
        """Show advanced search dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Advanced Search")
        dialog.geometry("600x400")
        
        ttk.Label(dialog, text="Search Criteria:").pack(pady=10)
        
        criteria_frame = ttk.Frame(dialog)
        criteria_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(criteria_frame, text="Name contains:").grid(row=0, column=0, sticky=tk.W)
        name_entry = ttk.Entry(criteria_frame)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(criteria_frame, text="Type:").grid(row=1, column=0, sticky=tk.W)
        type_combobox = ttk.Combobox(criteria_frame, values=list(set(EXTENSION_FOLDERS.values())))
        type_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(criteria_frame, text="Size (MB):").grid(row=2, column=0, sticky=tk.W)
        
        size_frame = ttk.Frame(criteria_frame)
        size_frame.grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        size_min = ttk.Entry(size_frame, width=8)
        size_min.pack(side=tk.LEFT)
        ttk.Label(size_frame, text="to").pack(side=tk.LEFT, padx=5)
        size_max = ttk.Entry(size_frame, width=8)
        size_max.pack(side=tk.LEFT)
        
        criteria_frame.columnconfigure(1, weight=1)
        
        # Results area
        results_frame = ttk.LabelFrame(dialog, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        results_tree = ttk.Treeview(results_frame, columns=('name', 'size', 'type'), 
                                  selectmode='browse')
        results_tree.heading('#0', text='')
        results_tree.heading('name', text='File Name')
        results_tree.heading('size', text='Size')
        results_tree.heading('type', text='Type')
        
        results_tree.column('#0', width=0, stretch=tk.NO)
        results_tree.column('name', width=300)
        results_tree.column('size', width=100)
        results_tree.column('type', width=100)
        
        scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        results_tree.configure(yscrollcommand=scroll_y.set)
        
        results_tree.pack(fill=tk.BOTH, expand=True)
        
        def perform_search():
            """Perform the advanced search"""
            name_query = name_entry.get().lower()
            type_query = type_combobox.get()
            min_size = size_min.get()
            max_size = size_max.get()
            
            results_tree.delete(*results_tree.get_children())
            
            for root, dirs, files in os.walk(self.current_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check name
                    if name_query and name_query not in file.lower():
                        continue
                    
                    # Check type
                    ext = os.path.splitext(file)[1].lower()
                    file_type = EXTENSION_FOLDERS.get(ext, 'Other')
                    if type_query and file_type != type_query:
                        continue
                    
                    # Check size
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if min_size:
                        try:
                            if size_mb < float(min_size):
                                continue
                        except ValueError:
                            pass
                    if max_size:
                        try:
                            if size_mb > float(max_size):
                                continue
                        except ValueError:
                            pass
                    
                    # Add to results
                    results_tree.insert('', tk.END, 
                                      values=(file, self.format_size(os.path.getsize(file_path)), 
                                              file_type))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Search", command=perform_search,
                  style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
    
    # ========== MEDIA PLAYBACK ==========
    def init_audio(self):
        """Initialize pygame for audio playback"""
        if not self.pygame_initialized:
            pygame.mixer.init()
            self.pygame_initialized = True
    
    def play_media(self):
        """Play selected media file"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            filepath = os.path.join(self.current_folder, filename)
            
            if filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                try:
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.play()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not play audio: {str(e)}")
            elif filename.lower().endswith(('.mp4', '.avi', '.mov')):
                try:
                    os.startfile(filepath)
                except:
                    messagebox.showerror("Error", "Could not play video")
    
    def stop_media(self):
        """Stop media playback"""
        if self.pygame_initialized:
            pygame.mixer.music.stop()
    
    # ========== SETTINGS AND CONFIG ==========
    def open_settings_dialog(self):
        """Open settings dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Settings")
        dialog.geometry("500x400")
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Appearance tab
        appearance_tab = ttk.Frame(notebook)
        notebook.add(appearance_tab, text="Appearance")
        
        ttk.Label(appearance_tab, text="Theme:").pack(pady=(10, 0))
        
        theme_var = tk.StringVar(value=self.settings['theme'])
        for theme in THEMES.keys():
            rb = ttk.Radiobutton(appearance_tab, text=theme, variable=theme_var, value=theme,
                                command=lambda: self.change_theme(theme_var.get()))
            rb.pack(anchor=tk.W, padx=20)
        
        # Features tab
        features_tab = ttk.Frame(notebook)
        notebook.add(features_tab, text="Features")
        
        ai_var = tk.BooleanVar(value=self.settings['ai_enabled'])
        cb = ttk.Checkbutton(features_tab, text="Enable AI Features", variable=ai_var,
                            command=lambda: self.toggle_setting('ai_enabled', ai_var.get()))
        cb.pack(anchor=tk.W, padx=20, pady=5)
        
        auto_var = tk.BooleanVar(value=self.settings['auto_clean'])
        cb = ttk.Checkbutton(features_tab, text="Auto Clean Suggestions", variable=auto_var,
                            command=lambda: self.toggle_setting('auto_clean', auto_var.get()))
        cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # Save button
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save Settings", command=lambda: self.save_settings(dialog),
                  style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def change_theme(self, theme):
        """Change application theme"""
        if theme in THEMES:
            self.settings['theme'] = theme
            self.apply_theme()
    
    def toggle_setting(self, setting, value):
        """Toggle a boolean setting"""
        self.settings[setting] = value
    
    def save_settings(self, dialog):
        """Save settings to config file"""
        try:
            with open('filemanager_config.json', 'w') as f:
                json.dump(self.settings, f)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {str(e)}")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists('filemanager_config.json'):
                with open('filemanager_config.json', 'r') as f:
                    self.settings.update(json.load(f))
        except:
            pass
    
    # ========== UTILITY METHODS ==========
    def update_storage_stats(self):
        """Update storage statistics display"""
        path = self.current_folder
        if not path or not os.path.isdir(path):
            return
        
        try:
            total_size = 0
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    total_size += os.path.getsize(item_path)
            
            # Show storage prediction
            prediction = self.storage_predictor.predict_usage(path)
            if prediction:
                pred_text = f"Predicted: {self.format_size(prediction)} in 3 months"
                self.status_text.set(f"{self.format_size(total_size)} used | {pred_text}")
            else:
                self.status_text.set(f"{self.format_size(total_size)} used")
        except Exception as e:
            print(f"Error updating storage stats: {str(e)}")
    
    def format_size(self, size):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def save_file_note(self, event=None):
        """Save note for selected file"""
        selected = self.file_list.selection()
        if selected:
            item = self.file_list.item(selected[0])
            filename = item['values'][0]
            
            note = self.notes_text.get(1.0, tk.END).strip()
            # In a real app, this would save to a database or file
            self.status_text.set(f"Note saved for {filename}")
    
    def show_help(self):
        """Show help information"""
        webbrowser.open("https://example.com/filemanager-help")
    
    def on_closing(self):
        """Handle window closing"""
        self.save_settings(self)
        self.destroy()

# ========== RUN APPLICATION ==========
if __name__ == "__main__":
    app = ModernFileManager()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()