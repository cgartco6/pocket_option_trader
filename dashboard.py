# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import time
from datetime import datetime, timedelta
import pytz
import os
import sys
import platform
from signal_generator import TradingSignalGenerator
from config import *

class TradingSignalDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Pocket Option Professional Trader")
        
        # Windows 10 Pro specific optimizations
        if platform.system() == 'Windows':
            self.root.state('zoomed')  # Start maximized
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass  # Older Windows versions
        
        # Initialize application
        self.setup_ui()
        self.signal_generator = TradingSignalGenerator()
        self.active_signals = {}
        self.last_signals = {}
        self.last_update = datetime.now(pytz.utc)
        self.refresh_signals()

    def setup_ui(self):
        """Configure UI based on theme"""
        # Set theme colors
        self.bg_color = "#1e1e1e" if UI_THEME == "dark" else "#f0f0f0"
        self.fg_color = "#dcdcdc" if UI_THEME == "dark" else "#1e1e1e"
        self.accent_color = "#2d2d30" if UI_THEME == "dark" else "#e1e1e1"
        self.header_color = "#3e3e42" if UI_THEME == "dark" else "#0078d7"
        self.status_color = "#252526" if UI_THEME == "dark" else "#e5e5e5"
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        self.root.geometry("1280x720")
        
        # Create custom styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        self.style.configure(
            '.', 
            background=self.bg_color,
            foreground=self.fg_color,
            font=('Segoe UI', 10)
        )
        
        self.style.configure(
            'Header.TFrame', 
            background=self.header_color
        )
        
        self.style.configure(
            'Header.TLabel', 
            background=self.header_color,
            foreground='white',
            font=('Segoe UI', 14, 'bold')
        )
        
        self.style.configure(
            'Status.TFrame', 
            background=self.status_color
        )
        
        self.style.configure(
            'Status.TLabel', 
            background=self.status_color,
            foreground=self.fg_color,
            font=('Segoe UI', 9)
        )
        
        self.style.configure(
            'Treeview', 
            font=('Segoe UI', 10),
            rowheight=28,
            fieldbackground=self.bg_color,
            background=self.bg_color,
            foreground=self.fg_color
        )
        
        self.style.configure(
            'Treeview.Heading', 
            font=('Segoe UI', 10, 'bold'),
            background="#0078d7",
            foreground="white"
        )
        
        self.style.map(
            'Treeview.Heading', 
            background=[('active', '#005a9e')]
        )
        
        # Build UI components
        self.create_header()
        self.create_main_panel()
        self.create_status_bar()
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_header(self):
        """Create header section"""
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        
        # Title
        title_label = ttk.Label(
            header_frame, 
            text="POCKET OPTION PROFESSIONAL TRADER",
            style='Header.TLabel'
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Strategy info
        strategy_text = (
            f"Strategy: RSI({RSI_PERIOD}) | "
            f"MACD({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL}) | "
            f"Assets: {len(TRADING_PAIRS)} Pairs"
        )
        strategy_label = ttk.Label(
            header_frame,
            text=strategy_text,
            style='Header.TLabel'
        )
        strategy_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Refresh button
        refresh_btn = ttk.Button(
            header_frame,
            text="⟳ Refresh Now",
            command=self.manual_refresh
        )
        refresh_btn.pack(side=tk.RIGHT, padx=10, pady=5)

    def create_main_panel(self):
        """Create main content area"""
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        # Create notebook for multiple tables
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pure Signals Tab
        pure_frame = ttk.Frame(notebook)
        notebook.add(pure_frame, text="Pure Trading Signals")
        self.create_pure_signal_table(pure_frame)
        
        # Confirmation Tab
        confirm_frame = ttk.Frame(notebook)
        notebook.add(confirm_frame, text="Trade Confirmation")
        self.create_confirmation_table(confirm_frame)
        
        # Active Signals Tab
        active_frame = ttk.Frame(notebook)
        notebook.add(active_frame, text="Active Signals")
        self.create_active_signals_table(active_frame)

    def create_pure_signal_table(self, parent):
        """Create pure signals table"""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        columns = ("pair", "signal", "signal_time")
        
        self.pure_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Set column headings
        self.pure_tree.heading("pair", text="Trading Pair", anchor=tk.CENTER)
        self.pure_tree.heading("signal", text="Signal", anchor=tk.CENTER)
        self.pure_tree.heading("signal_time", text="Signal Time (UTC)", anchor=tk.CENTER)
        
        # Set column widths
        self.pure_tree.column("pair", width=180, anchor=tk.CENTER)
        self.pure_tree.column("signal", width=120, anchor=tk.CENTER)
        self.pure_tree.column("signal_time", width=220, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient=tk.VERTICAL, 
            command=self.pure_tree.yview
        )
        self.pure_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pure_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.pure_tree.tag_configure('BUY', background='#e8f5e9', foreground='#2e7d32')
        self.pure_tree.tag_configure('SELL', background='#ffebee', foreground='#c62828')
        self.pure_tree.tag_configure('HOLD', background='#e3f2fd', foreground='#1565c0')
        self.pure_tree.tag_configure('ERROR', background='#f5f5f5', foreground='#9e9e9e')

    def create_confirmation_table(self, parent):
        """Create confirmation table"""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        columns = ("pair", "signal", "direction", "duration")
        
        self.confirm_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Set column headings
        self.confirm_tree.heading("pair", text="Trading Pair", anchor=tk.CENTER)
        self.confirm_tree.heading("signal", text="Signal", anchor=tk.CENTER)
        self.confirm_tree.heading("direction", text="Confirmation", anchor=tk.CENTER)
        self.confirm_tree.heading("duration", text="Duration", anchor=tk.CENTER)
        
        # Set column widths
        self.confirm_tree.column("pair", width=180, anchor=tk.CENTER)
        self.confirm_tree.column("signal", width=120, anchor=tk.CENTER)
        self.confirm_tree.column("direction", width=180, anchor=tk.CENTER)
        self.confirm_tree.column("duration", width=180, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient=tk.VERTICAL, 
            command=self.confirm_tree.yview
        )
        self.confirm_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.confirm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.confirm_tree.tag_configure('CONFIRMED', background='#e8f5e9', foreground='#2e7d32')
        self.confirm_tree.tag_configure('REVERSED', background='#ffebee', foreground='#c62828')
        self.confirm_tree.tag_configure('PENDING', background='#fff9c4', foreground='#f57f17')
        self.confirm_tree.tag_configure('N/A', background='#f5f5f5', foreground='#9e9e9e')

    def create_active_signals_table(self, parent):
        """Create active signals table"""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        columns = ("pair", "signal", "entry_time", "duration", "status")
        
        self.active_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Set column headings
        self.active_tree.heading("pair", text="Trading Pair", anchor=tk.CENTER)
        self.active_tree.heading("signal", text="Signal", anchor=tk.CENTER)
        self.active_tree.heading("entry_time", text="Entry Time", anchor=tk.CENTER)
        self.active_tree.heading("duration", text="Duration", anchor=tk.CENTER)
        self.active_tree.heading("status", text="Status", anchor=tk.CENTER)
        
        # Set column widths
        self.active_tree.column("pair", width=150, anchor=tk.CENTER)
        self.active_tree.column("signal", width=100, anchor=tk.CENTER)
        self.active_tree.column("entry_time", width=180, anchor=tk.CENTER)
        self.active_tree.column("duration", width=120, anchor=tk.CENTER)
        self.active_tree.column("status", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient=tk.VERTICAL, 
            command=self.active_tree.yview
        )
        self.active_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.active_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.active_tree.tag_configure('ACTIVE', background='#e3f2fd', foreground='#1565c0')
        self.active_tree.tag_configure('PROFIT', background='#e8f5e9', foreground='#2e7d32')
        self.active_tree.tag_configure('LOSS', background='#ffebee', foreground='#c62828')
        self.active_tree.tag_configure('CLOSED', background='#f5f5f5', foreground='#9e9e9e')

    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ttk.Frame(self.root, style='Status.TFrame')
        status_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(5, 10))
        
        # Status labels
        self.update_label = ttk.Label(
            status_frame, 
            text="Last update: Initializing...",
            style='Status.TLabel'
        )
        self.update_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.next_label = ttk.Label(
            status_frame, 
            text="Next refresh: --:--:--",
            style='Status.TLabel'
        )
        self.next_label.pack(side=tk.LEFT, padx=20, pady=2)
        
        self.candle_label = ttk.Label(
            status_frame, 
            text="Next candle: --:--:--",
            style='Status.TLabel'
        )
        self.candle_label.pack(side=tk.RIGHT, padx=10, pady=2)

    def refresh_signals(self):
        """Periodically refresh trading signals"""
        def update_task():
            try:
                start_time = time.time()
                signals = self.signal_generator.get_all_signals()
                update_time = datetime.now(pytz.utc)
                next_refresh = update_time + timedelta(seconds=REFRESH_INTERVAL)
                
                # Update UI
                self.root.after(0, self.update_ui, signals, update_time, next_refresh)
                
                # Update active signals
                self.update_active_signals(signals)
                
                # Log performance
                elapsed = time.time() - start_time
                print(f"Signal refresh completed in {elapsed:.2f} seconds")
                
            except Exception as e:
                self.root.after(0, self.show_error, "Refresh Error", str(e))
            finally:
                # Schedule next refresh
                self.root.after(REFRESH_INTERVAL * 1000, self.refresh_signals)
        
        # Run in background thread
        threading.Thread(target=update_task, daemon=True).start()

    def manual_refresh(self):
        """Trigger manual refresh"""
        self.status_label.config(text="Status: Manual refresh requested...")
        threading.Thread(target=self.refresh_signals, daemon=True).start()

    def update_ui(self, signals, update_time, next_refresh):
        """Update all UI elements with new data"""
        # Clear tables
        for tree in [self.pure_tree, self.confirm_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # Update pure signals table
        for pair, (signal, signal_time, direction, duration) in signals.items():
            time_str = signal_time.strftime("%Y-%m-%d %H:%M:%S") if signal_time else "N/A"
            self.pure_tree.insert(
                "", tk.END, 
                values=(pair, signal, time_str),
                tags=(signal,)
            )
            
            # Update confirmation table
            if signal in ("BUY", "SELL"):
                self.confirm_tree.insert(
                    "", tk.END, 
                    values=(pair, signal, direction or "N/A", duration or "N/A"),
                    tags=(direction,)
                )
        
        # Update status bar
        self.update_label.config(
            text=f"Last update: {update_time.strftime('%H:%M:%S UTC')}"
        )
        self.next_label.config(
            text=f"Next refresh: {next_refresh.strftime('%H:%M:%S UTC')}"
        )
        self.candle_label.config(
            text=f"Next candle: {self.get_next_candle_time()}"
        )
        
        # Store for active signal tracking
        self.last_signals = signals
        self.last_update = update_time

    def update_active_signals(self, signals):
        """Track and update active signals"""
        current_time = datetime.now(pytz.utc)
        new_signals = []
        
        # Add new signals
        for pair, (signal, signal_time, _, _) in signals.items():
            if signal in ("BUY", "SELL") and pair not in self.active_signals:
                self.active_signals[pair] = {
                    "signal": signal,
                    "entry_time": signal_time or current_time,
                    "status": "ACTIVE"
                }
                new_signals.append(pair)
        
        # Update existing signals
        for pair in list(self.active_signals.keys()):
            signal_data = self.active_signals[pair]
            
            # Check if signal is still valid
            current_signal = signals.get(pair, ("HOLD",))[0]
            if current_signal != signal_data["signal"]:
                # Determine if profitable
                if current_signal == "HOLD":
                    signal_data["status"] = "CLOSED"
                elif (signal_data["signal"] == "BUY" and current_signal == "SELL") or \
                     (signal_data["signal"] == "SELL" and current_signal == "BUY"):
                    signal_data["status"] = "LOSS"
                else:
                    signal_data["status"] = "CLOSED"
        
        # Update table
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)
            
        for pair, data in self.active_signals.items():
            duration = current_time - data["entry_time"]
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            
            self.active_tree.insert(
                "", tk.END,
                values=(
                    pair,
                    data["signal"],
                    data["entry_time"].strftime("%H:%M:%S"),
                    duration_str,
                    data["status"]
                ),
                tags=(data["status"],)
            )
            
            # Clean up closed signals
            if data["status"] in ("CLOSED", "LOSS", "PROFIT"):
                if (current_time - data["entry_time"]) > timedelta(minutes=30):
                    del self.active_signals[pair]

    def get_next_candle_time(self):
        """Calculate time until next candle"""
        now = datetime.utcnow()
        current_minute = now.minute
        remainder = current_minute % 5
        next_candle_min = 5 - remainder
        next_time = now + timedelta(minutes=next_candle_min)
        return next_time.strftime("%H:%M:%S UTC")

    def show_error(self, title, message):
        """Show error message"""
        messagebox.showerror(title, f"{message}\n\nApplication will continue running.")

# ==============================
# APPLICATION ENTRY POINT
# ==============================
if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    
    # Initialize and run application
    app = TradingSignalDashboard(root)
    
    # Windows-specific optimizations
    if platform.system() == 'Windows':
        # Set taskbar icon
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'
            
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except:
                pass
    
    # Start main loop
    root.mainloop()
