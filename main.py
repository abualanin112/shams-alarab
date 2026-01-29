from app.ui.main_window import MainWindow
from app.core.config import Config, GPUNotAvailableError
import tkinter as tk
from tkinter import messagebox
import sys

if __name__ == "__main__":
    try:
        # Bootstrap: Strict GPU Contract Enforcement
        Config.require_gpu_support()
        
        app = MainWindow()
        app.mainloop()
        
    except GPUNotAvailableError as e:
        # Since GUI might not be initialized, use a temporary root for messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Fatal Error: GPU Required", str(e))
        root.destroy()
        sys.exit(1)
    except Exception as e:
        # Fallback for other critical startup errors
        print(f"Critical Startup Error: {e}") 
        sys.exit(1)
