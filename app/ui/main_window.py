import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import queue
import logging
import os
from ..pipeline.pipeline import VideoPipeline
from ..core.utils import get_output_path
from ..core.config import Config

logger = logging.getLogger(__name__)

class TextHandler(logging.Handler):
    """Logging handler that writes to a Queue."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Processor App")
        self.geometry("800x600")
        
        # Data
        self.video_files = []
        self.logo_path = None
        self.queue = queue.Queue()
        self.pipeline = VideoPipeline()
        self.is_processing = False
        
        # Logging setup
        self.setup_logging()
        
        # UI Setup
        self.create_widgets()
        
        # Start periodic check for log messages
        self.after(100, self.process_queue)

    def setup_logging(self):
        """Redirect logging to our queue."""
        handler = TextHandler(self.queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to the pipeline logger and others if needed
        # We assume root logger for simplicity or specific loggers
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    def create_widgets(self):
        # --- File Selection Frame ---
        file_frame = ttk.LabelFrame(self, text="Input Videos")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.files_listbox = tk.Listbox(file_frame, height=5)
        self.files_listbox.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(side="right", fill="y")
        
        ttk.Button(btn_frame, text="Add Videos", command=self.add_videos).pack(pady=2)
        ttk.Button(btn_frame, text="Clear", command=self.clear_videos).pack(pady=2)

        # --- Watermark Selection ---
        logo_frame = ttk.LabelFrame(self, text="Watermark")
        logo_frame.pack(fill="x", padx=10, pady=5)
        
        self.logo_label = ttk.Label(logo_frame, text="No logo selected")
        self.logo_label.pack(side="left", padx=5)
        
        ttk.Button(logo_frame, text="Select Logo", command=self.select_logo).pack(side="right", padx=5, pady=5)

        # --- Controls ---
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="START PROCESSING", command=self.start_processing)
        self.start_btn.pack(side="left", fill="x", expand=True)

        # --- Progress ---
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # --- Logs ---
        log_frame = ttk.LabelFrame(self, text="Logs")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=10)
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

    def add_videos(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov")])
        for f in files:
            if f not in self.video_files:
                self.video_files.append(f)
                self.files_listbox.insert(tk.END, os.path.basename(f))

    def clear_videos(self):
        self.video_files = []
        self.files_listbox.delete(0, tk.END)

    def select_logo(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png")])
        if f:
            self.logo_path = f
            self.logo_label.config(text=os.path.basename(f))

    def process_queue(self):
        """Handle log messages from the queue."""
        try:
            while True:
                msg = self.queue.get_nowait()
                self.log_area.config(state='normal')
                self.log_area.insert(tk.END, msg + '\n')
                self.log_area.see(tk.END)
                self.log_area.config(state='disabled')
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def set_ui_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.start_btn.config(state=state)
        # We might want to disable add/clear buttons too
        
    def start_processing(self):
        if not self.video_files:
            messagebox.showwarning("No Videos", "Please select video files first.")
            return
            
        self.is_processing = True
        self.set_ui_state(False)
        self.progress['value'] = 0
        self.progress['maximum'] = 100 # We now use percentage (0-100) across all files
        
        # Run in thread
        thread = threading.Thread(target=self.run_pipeline)
        thread.start()

    def run_pipeline(self):
        failed_videos = []
        try:
            total_files = len(self.video_files)
            
            for i, video_path in enumerate(list(self.video_files)):
                filename = os.path.basename(video_path)
                try:
                    output_path = get_output_path(video_path)
                    
                    self.queue.put(f"Starting: {filename}")
                    
                    # Define callback for this specific file
                    def update_progress(p):
                        file_weight = 100 / total_files
                        base = i * file_weight
                        actual = base + (p / 100 * file_weight)
                        self.after(0, lambda v=actual, t=f"{int(p)}%": self._update_ui_progress(v, t))

                    self.pipeline.process_video(video_path, output_path, self.logo_path, progress_callback=update_progress)
                    self.queue.put(f"Finished: {filename}")
                    
                    # Auto-Removal Logic (UX Enhancement)
                    if Config.AUTO_REMOVE_AFTER_SUCCESS:
                        self.after(0, lambda p=video_path: self.remove_video_from_list(p))
                        
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {str(e)}")
                    failed_videos.append((filename, str(e)))
                    self.queue.put(f"FAILED: {filename} - {str(e)}")
            
            if not failed_videos:
                self.queue.put("ALL TASKS COMPLETED SUCCESSFULLY.")
            else:
                summary = "\n".join([f"- {name}: {err}" for name, err in failed_videos])
                self.queue.put(f"COMPLETED WITH {len(failed_videos)} ERRORS:\n{summary}")
            
        except Exception as e:
            self.queue.put(f"CRITICAL ERROR: {str(e)}")
            logging.exception("Pipeline orchestration failed")
        finally:
            self.is_processing = False
            self.after(0, lambda: self.set_ui_state(True))
            self.after(0, lambda: self.progress.configure(value=0)) # Reset
            
            if failed_videos:
                error_msg = f"Processing finished with {len(failed_videos)} errors:\n\n"
                error_msg += "\n".join([f"• {name}" for name, _ in failed_videos])
                self.after(0, lambda: messagebox.showwarning("Processing Issues", error_msg))
            else:
                self.after(0, lambda: messagebox.showinfo("Done", "Processing Complete Successfully"))

    def _update_ui_progress(self, value, text):
        self.progress['value'] = value
        # Optional: could add a label for text if created, but prompt said "progress bar move".
        # Value move is sufficient.

    def remove_video_from_list(self, video_path: str):
        """
        Thread-safe removal of a video from the listbox and internal list.
        """
        try:
            if video_path in self.video_files:
                index = self.video_files.index(video_path)
                self.video_files.remove(video_path)
                self.files_listbox.delete(index)
                logger.info(f"UI Clean: Removed {os.path.basename(video_path)} from list.")
                
                # If list is empty, reset progress
                if not self.video_files:
                    self.progress['value'] = 0
            else:
                 logger.debug(f"UI Clean: {video_path} not found in list (already removed?).")
        except Exception as e:
            logger.error(f"UI Clean Error: Failed to remove video {video_path} - {e}")
