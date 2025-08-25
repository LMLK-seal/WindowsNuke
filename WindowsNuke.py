import customtkinter as ctk
import os
import shutil
import psutil
import ctypes
import subprocess
import threading
import tkinter.messagebox as messagebox
import stat
import errno

# Define the folders typically associated with a Windows installation
WINDOWS_FOLDERS = [
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "$Recycle.Bin",
    "Users" # This is risky, but where most user data is. We will handle it carefully.
]

# Define system files in the root that can be deleted
WINDOWS_ROOT_FILES = [
    "pagefile.sys",
    "swapfile.sys",
    "hiberfil.sys"
]

class WindowsRemoverApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Basic App Configuration ---
        self.title("WindowsNuke - Windows Remover tool")
        self.geometry("700x750")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.scan_results = {} # Use a dictionary for easier size lookups
        self.selected_size_gb = 0.0
        self.selected_drive = None

        # --- Check for Admin Privileges ---
        if not self.is_admin():
            messagebox.showerror("Permission Denied", "This program requires Administrator privileges to function. Please right-click and 'Run as administrator'.")
            self.after(100, self.destroy)
            return

        # --- GUI Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header and Warning Frame
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        title_label = ctk.CTkLabel(header_frame, text="WindowsNuke - Windows Remover tool", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        warning_label = ctk.CTkLabel(
            header_frame,
            text="⚠️ DANGER: This tool deletes system files. Double-check your drive selection.\n"
                 "The SAFEST method is to manually back up data and FORMAT the drive.",
            text_color="orange",
            font=ctk.CTkFont(size=12)
        )
        warning_label.pack(pady=(0, 10))

        # 2. Drive Selection Frame
        drive_frame = ctk.CTkFrame(self)
        drive_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        drive_frame.grid_columnconfigure(1, weight=1)

        drive_label = ctk.CTkLabel(drive_frame, text="Select Target Drive:")
        drive_label.grid(row=0, column=0, padx=10, pady=10)

        self.drives_menu = ctk.CTkOptionMenu(drive_frame, values=self.get_available_drives(), command=self.on_drive_select)
        self.drives_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.drives_menu.set("Select a drive...")

        self.scan_button = ctk.CTkButton(drive_frame, text="Scan for Windows Installation", command=self.start_scan_thread, state="disabled")
        self.scan_button.grid(row=0, column=2, padx=10, pady=10)

        # 3. Results Display Frame
        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        selection_helper_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        selection_helper_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        results_label = ctk.CTkLabel(selection_helper_frame, text="Scan Results: Check items to delete", font=ctk.CTkFont(weight="bold"))
        results_label.pack(side="left")

        self.deselect_all_button = ctk.CTkButton(selection_helper_frame, text="Deselect All", width=100, command=self.deselect_all, state="disabled")
        self.deselect_all_button.pack(side="right", padx=(5,0))
        
        self.select_all_button = ctk.CTkButton(selection_helper_frame, text="Select All", width=100, command=self.select_all, state="disabled")
        self.select_all_button.pack(side="right")
        
        self.scrollable_results_frame = ctk.CTkScrollableFrame(results_frame, label_text="")
        self.scrollable_results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_results_frame.grid_columnconfigure(1, weight=1)

        # 4. Action & Progress Frame
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1) # Makes progress bar expand

        # --- Action Widgets (visible by default) ---
        self.delete_button = ctk.CTkButton(self.action_frame, text="DELETE Selected Files & Folders", command=self.start_delete_thread, fg_color="red", hover_color="darkred", state="disabled")
        self.delete_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.selected_size_label = ctk.CTkLabel(self.action_frame, text="Selected Size: 0.00 GB", anchor="e")
        self.selected_size_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # --- Progress Widgets (hidden by default) ---
        self.progress_label = ctk.CTkLabel(self.action_frame, text="Deleting...", anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.set(0)

        # 5. Status Bar
        self.status_label = ctk.CTkLabel(self, text="Please select a drive to begin.", anchor="w")
        self.status_label.grid(row=4, column=0, padx=20, pady=5, sticky="ew")


    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def get_available_drives(self):
        drives = []
        system_drive = os.getenv('SystemDrive', 'C:').upper()
        for part in psutil.disk_partitions():
            if part.fstype and 'rw' in part.opts:
                if part.mountpoint.upper() != system_drive.upper():
                    drives.append(part.mountpoint)
        return drives

    def on_drive_select(self, drive):
        self.selected_drive = drive
        self.scan_button.configure(state="normal")
        self.status_label.configure(text=f"Drive {drive} selected. Ready to scan.")
        self.clear_results_frame()
        self.scan_results = {}
        self.update_selection_totals()
        self.delete_button.configure(state="disabled")

    def clear_results_frame(self):
        for widget in self.scrollable_results_frame.winfo_children():
            widget.destroy()

    def update_status(self, message):
        self.status_label.configure(text=message)

    def select_all(self):
        for item in self.scan_results.values():
            item['checkbox_var'].set(True)
        self.update_selection_totals()

    def deselect_all(self):
        for item in self.scan_results.values():
            item['checkbox_var'].set(False)
        self.update_selection_totals()

    def update_selection_totals(self):
        total_bytes = 0
        selected_count = 0
        for item in self.scan_results.values():
            if item['checkbox_var'].get():
                total_bytes += item['size_bytes']
                selected_count += 1
        
        self.selected_size_gb = total_bytes / (1024**3)
        self.selected_size_label.configure(text=f"Selected Size: {self.selected_size_gb:.2f} GB")

        self.delete_button.configure(state="normal" if selected_count > 0 else "disabled")
        
        if self.scan_results:
            self.select_all_button.configure(state="normal")
            self.deselect_all_button.configure(state="normal")
        else:
            self.select_all_button.configure(state="disabled")
            self.deselect_all_button.configure(state="disabled")

    def get_folder_size(self, path):
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            continue
        except PermissionError:
            self.update_status(f"Warning: Permission denied for parts of {path}. Size may be inaccurate.")
        return total_size

    def handle_remove_readonly(self, func, path, exc_info):
        excvalue = exc_info[1]
        if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            func(path)
        else:
            raise

    # --- Threaded Operations ---

    def start_scan_thread(self):
        self.scan_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.clear_results_frame()
        self.scan_results = {}
        self.update_selection_totals()
        self.update_status(f"Scanning {self.selected_drive} for Windows installation... This may take a while.")
        
        thread = threading.Thread(target=self.scan_drive, daemon=True)
        thread.start()

    def scan_drive(self):
        drive = self.selected_drive
        temp_scan_results = []
        
        if not os.path.exists(os.path.join(drive, "Windows", "System32")):
            self.after(0, self.update_status, f"Error: No Windows installation found on {drive}.")
            self.after(0, lambda: messagebox.showerror("Scan Failed", f"The drive {drive} does not appear to contain a Windows installation."))
            self.after(0, self.scan_button.configure, {"state": "normal"})
            return

        all_items = [(f, "folder") for f in WINDOWS_FOLDERS] + [(f, "file") for f in WINDOWS_ROOT_FILES]

        for name, item_type in all_items:
            path = os.path.join(drive, name)
            self.after(0, self.update_status, f"Scanning: {path}...")
            if os.path.exists(path):
                size_bytes = 0
                if item_type == "folder":
                    size_bytes = self.get_folder_size(path)
                else:
                    try:
                        size_bytes = os.path.getsize(path)
                    except OSError:
                        continue
                
                # Only add if size > 0 or it's the Recycle Bin which is often 0
                if size_bytes > 0 or "$Recycle.Bin" in name:
                    temp_scan_results.append({'path': path, 'size_bytes': size_bytes})

        self.after(0, self.display_scan_results, temp_scan_results)

    def display_scan_results(self, results):
        self.clear_results_frame()
        self.scan_results = {}

        if not results:
            self.update_status(f"Scan complete. No Windows files found on {self.selected_drive}.")
            ctk.CTkLabel(self.scrollable_results_frame, text="No Windows-related folders or files found.").pack(padx=10, pady=10)
            self.scan_button.configure(state="normal")
            return

        users_folder_found = any('Users' == os.path.basename(item['path']) for item in results)
        if users_folder_found:
            warning_label = ctk.CTkLabel(self.scrollable_results_frame, text="⚠️ WARNING: 'Users' folder contains personal data. Deselect to keep it.", text_color="orange")
            warning_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        for i, item in enumerate(results):
            row_index = i + 1 if users_folder_found else i
            path = item['path']

            self.scan_results[path] = {
                'size_bytes': item['size_bytes'],
                'checkbox_var': ctk.BooleanVar(value=True)
            }
            # Uncheck Users folder by default for safety
            if os.path.basename(path) == 'Users':
                self.scan_results[path]['checkbox_var'].set(False)

            checkbox = ctk.CTkCheckBox(self.scrollable_results_frame, text="", variable=self.scan_results[path]['checkbox_var'], command=self.update_selection_totals)
            checkbox.grid(row=row_index, column=0, padx=(5,0), pady=2, sticky="w")
            path_label = ctk.CTkLabel(self.scrollable_results_frame, text=path, anchor="w")
            path_label.grid(row=row_index, column=1, padx=5, pady=2, sticky="ew")
            size_gb = item['size_bytes'] / (1024**3)
            size_label = ctk.CTkLabel(self.scrollable_results_frame, text=f"{size_gb:.2f} GB", anchor="e", font=ctk.CTkFont(family="Consolas"))
            size_label.grid(row=row_index, column=2, padx=5, pady=2, sticky="e")

        self.update_status("Scan complete. Review the files below before deleting.")
        self.scan_button.configure(state="normal")
        self.update_selection_totals()

    def switch_to_progress_view(self, show_progress=True):
        """Switches the action frame between delete button and progress bar."""
        if show_progress:
            self.delete_button.grid_remove()
            self.selected_size_label.grid_remove()
            self.progress_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            self.progress_bar.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        else:
            self.progress_label.grid_remove()
            self.progress_bar.grid_remove()
            self.delete_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            self.selected_size_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")
            self.update_selection_totals()

    def start_delete_thread(self):
        if self.selected_size_gb == 0:
            messagebox.showwarning("No Selection", "No files or folders are selected for deletion.")
            return

        if not messagebox.askyesno("FINAL CONFIRMATION", f"You are about to permanently delete {self.selected_size_gb:.2f} GB of data from drive {self.selected_drive}.\n\nTHIS ACTION CANNOT BE UNDONE.\n\nAre you absolutely sure?"):
            return
            
        self.scan_button.configure(state="disabled")
        self.drives_menu.configure(state="disabled")
        self.select_all_button.configure(state="disabled")
        self.deselect_all_button.configure(state="disabled")
        self.switch_to_progress_view(True)

        thread = threading.Thread(target=self.delete_files, daemon=True)
        thread.start()

    def delete_files(self):
        paths_to_delete = [path for path, item in self.scan_results.items() if item['checkbox_var'].get()]
        total_bytes_to_delete = sum(self.scan_results[path]['size_bytes'] for path in paths_to_delete)
        bytes_deleted = 0

        try:
            for i, path in enumerate(paths_to_delete):
                self.after(0, self.update_status, f"Taking ownership of {os.path.basename(path)}...")
                try:
                    # FIX: Use shell=True and quotes to handle paths with spaces
                    takeown_cmd = f'takeown /F "{path}" /R /D Y'
                    icacls_cmd = f'icacls "{path}" /grant "{os.getlogin()}:F" /T'
                    subprocess.run(takeown_cmd, check=True, capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(icacls_cmd, check=True, capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    self.after(0, self.update_status, f"Deleting ({i+1}/{len(paths_to_delete)}): {os.path.basename(path)}...")
                    if os.path.isdir(path):
                        shutil.rmtree(path, onerror=self.handle_remove_readonly)
                    elif os.path.isfile(path):
                        os.chmod(path, stat.S_IWRITE)
                        os.remove(path)
                    
                    # Update progress based on size
                    item_size = self.scan_results[path]['size_bytes']
                    bytes_deleted += item_size
                    progress = bytes_deleted / total_bytes_to_delete if total_bytes_to_delete > 0 else 1
                    deleted_gb = bytes_deleted / (1024**3)
                    total_gb = total_bytes_to_delete / (1024**3)

                    self.after(0, self.progress_bar.set, progress)
                    self.after(0, self.progress_label.configure, {"text": f"Deleted: {deleted_gb:.2f} / {total_gb:.2f} GB"})

                except (subprocess.CalledProcessError, OSError, PermissionError) as e:
                    error_detail = e.stderr.decode('utf-8', errors='ignore').strip() if hasattr(e, 'stderr') and e.stderr else str(e)
                    error_message = f"ERROR: Failed to delete {os.path.basename(path)}. Reason: {error_detail}"
                    self.after(0, self.update_status, error_message)
                    self.after(0, lambda: messagebox.showerror("Deletion Error", error_message + "\n\nSome files may remain. It's safer to format the drive."))
                    return # Stop the process

            final_message = f"Deletion complete. Reclaimed approx. {self.selected_size_gb:.2f} GB."
            self.after(0, self.update_status, final_message)
            self.after(0, self.clear_results_frame)
            self.after(0, lambda: ctk.CTkLabel(self.scrollable_results_frame, text=final_message + "\nYou can now close the program.").pack(padx=10, pady=10))
            self.after(0, lambda: messagebox.showinfo("Success", final_message))

        finally:
            # Always restore the UI state, even on error
            self.after(0, self.scan_button.configure, {"state": "normal"})
            self.after(0, self.drives_menu.configure, {"state": "normal"})
            self.after(0, self.switch_to_progress_view, False)
            self.after(0, self.scan_results.clear)
            self.after(0, self.update_selection_totals)

if __name__ == "__main__":
    app = WindowsRemoverApp()
    app.mainloop()
