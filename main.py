# main.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
import os
import threading
import time
from datetime import datetime
import hashlib

from wipe_methods import secure_delete_file, wipe_folder_recursive
from certificate_generator import generate_certificate
from drive_detection import list_drives

LOG_FILE = "logs/wipe_log.txt"
os.makedirs("logs", exist_ok=True)


def get_file_hash(file_path):
    """Calculate SHA256 hash of a file."""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return "N/A"
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return "Error"


def log_operation(file_path, method, status, wipe_time, hash_before, hash_after):
    """Log the wiping operation."""
    with open(LOG_FILE, "a") as log:
        log.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {file_path} | {method} | {status} | "
            f"Time Taken: {wipe_time:.2f}s | Hash Before: {hash_before} | Hash After: {hash_after}\n"
        )


def select_target():
    """Select a file or folder."""
    path = filedialog.askopenfilename(title="Select File")
    if not path:
        path = filedialog.askdirectory(title="Select Folder")
    target_var.set(path)


def show_success_popup(cert_path=None, wipe_time=None):
    """Popup after successful wipe."""
    popup = Toplevel(root)
    popup.title("Wipe Complete")
    popup.geometry("420x280")
    popup.configure(bg="white")

    tk.Label(popup, text="✅", font=("Arial", 50), fg="green", bg="white").pack(pady=10)
    tk.Label(popup, text="Data Wiped Successfully!", font=("Arial", 16, "bold"), bg="white", fg="green").pack()

    if wipe_time is not None:
        tk.Label(popup, text=f"Time Taken: {wipe_time:.2f} seconds", font=("Arial", 10), bg="white", fg="black").pack(pady=4)

    if cert_path:
        tk.Label(popup, text=f"Certificate saved at:\n{cert_path}", font=("Arial", 9), bg="white").pack(pady=8)

    tk.Button(
        popup, text="OK", command=popup.destroy,
        bg="#28a745", fg="white", width=14, height=1, font=("Arial", 10, "bold")
    ).pack(pady=12)


def update_progress(percent, status_text):
    """Update progress bar and status text."""
    def _ui_update():
        progress_var.set(percent)
        status_var.set(status_text)
    root.after(0, _ui_update)


def worker_wipe(path, passes, method_label, want_cert):
    """Perform wiping in a background thread."""
    try:
        update_progress(0, "Starting wipe...")

        wipe_start = datetime.now()
        wipe_start_str = wipe_start.strftime("%Y-%m-%d %H:%M:%S")

        hash_before = get_file_hash(path) if os.path.isfile(path) else "N/A"

        cert_path = None
        if os.path.isfile(path):
            ok = secure_delete_file(path, passes, update_progress)
            status = "Wiped" if ok else "Failed"
        else:
            ok = wipe_folder_recursive(path, passes, update_progress)
            status = "Wiped" if ok else "Failed"

        hash_after = get_file_hash(path) if os.path.isfile(path) else "N/A"

        wipe_end = datetime.now()
        wipe_end_str = wipe_end.strftime("%Y-%m-%d %H:%M:%S")
        wipe_time = (wipe_end - wipe_start).total_seconds()

        update_progress(100, "Verifying...")
        time.sleep(0.5)

        if want_cert and status == "Wiped":
            try:
                cert_path = generate_certificate(
                    target=path,
                    method=method_label,
                    status=status,
                    output_path="certificates",
                    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "logo.png")),
                    wipe_start=wipe_start_str,
                    wipe_end=wipe_end_str,
                    hash_before=hash_before,
                    hash_after=hash_after
                )

            except Exception as e:
                messagebox.showerror("Certificate Error", f"Could not generate certificate: {e}")
                cert_path = None

        log_operation(path, method_label, status, wipe_time, hash_before, hash_after)
        update_progress(100, "Complete ✅")
        root.after(0, lambda: show_success_popup(cert_path, wipe_time))

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Wipe failed: {e}"))
        update_progress(0, "Idle...")


def start_wipe():
    """Start wipe operation."""
    path = target_var.get()
    if not path or not os.path.exists(path):
        messagebox.showerror("Error", "Invalid path")
        return

    method = method_var.get()
    passes = 3 if "3 Passes" in method else 7 if "7 Passes" in method else 35
    want_cert = cert_var.get() == 1

    t = threading.Thread(target=worker_wipe, args=(path, passes, method, want_cert), daemon=True)
    t.start()


# ----- Tkinter UI -----
root = tk.Tk()
root.title("FormatX - Secure Data Wiping Tool")
root.geometry("550x580")
root.configure(bg="#f8f9fa")

target_var = tk.StringVar()
method_var = tk.StringVar(value="Random Overwrite (3 Passes)")
progress_var = tk.DoubleVar()
status_var = tk.StringVar(value="Idle...")
cert_var = tk.IntVar(value=1)

# Title
tk.Label(root, text="🔐 FormatX - Secure Data Wiping", font=("Arial", 20, "bold"), bg="#f8f9fa", fg="#343a40").pack(pady=15)

# Frame
frame = tk.Frame(root, bg="#f8f9fa")
frame.pack(pady=6)

# File selection
tk.Label(frame, text="Select File or Folder to Wipe", bg="#f8f9fa", fg="#495057", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
tk.Entry(frame, textvariable=target_var, width=58).grid(row=1, column=0, padx=5, pady=6, columnspan=2)
tk.Button(frame, text="Browse", command=select_target, bg="#dee2e6", fg="#212529", width=10).grid(row=1, column=2, padx=5)

# Wipe Method
tk.Label(frame, text="Wipe Method", bg="#f8f9fa", fg="#495057", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(8,0))
tk.OptionMenu(frame, method_var,
              "Random Overwrite (3 Passes)",
              "Random Overwrite (7 Passes)",
              "Random Overwrite (35 Passes)").grid(row=3, column=0, sticky="w", pady=4)

# Checkbox
tk.Checkbutton(frame, text="Generate Certificate After Wipe", variable=cert_var, bg="#f8f9fa", fg="#212529").grid(row=4, column=0, sticky="w", pady=4)

# Drive list
tk.Label(root, text="Detected Drives:", bg="#f8f9fa", fg="#495057", font=("Arial", 10, "bold")).pack(pady=(10,0))
drive_list_text = "\n".join(list_drives())
tk.Label(root, text=drive_list_text, fg="blue", bg="#f8f9fa", font=("Arial", 9)).pack()

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=420, mode="determinate", variable=progress_var)
progress_bar.pack(pady=18)

# Status text
tk.Label(root, textvariable=status_var, font=("Arial", 10, "italic"), bg="#f8f9fa", fg="gray").pack()

# Start button
tk.Button(root, text="Start Wipe", command=start_wipe, bg="#dc3545", fg="white", width=20, height=2, font=("Arial", 11, "bold")).pack(pady=18)

# Footer
tk.Label(root, text="© 2025 FormatX | Secure Data Wiping Tool", font=("Arial", 8), bg="#f8f9fa", fg="#6c757d").pack(side="bottom", pady=8)

root.mainloop()
