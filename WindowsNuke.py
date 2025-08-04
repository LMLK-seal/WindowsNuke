import customtkinter as ctk
import os
import shutil
import psutil
import ctypes
import subprocess
import threading
import tkinter.messagebox as messagebox

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
        self.geometry("700x650")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.found_folders = []
        self.found_files = []
        self.total_size_gb = 0.0
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
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        self.results_textbox = ctk.CTkTextbox(results_frame, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.results_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # 4. Action Frame
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.delete_button = ctk.CTkButton(action_frame, text="DELETE Found Files & Folders", command=self.start_delete_thread, fg_color="red", hover_color="darkred", state="disabled")
        self.delete_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # 5. Status Bar
        self.status_label = ctk.CTkLabel(self, text="Please select a drive to begin.", anchor="w")
        self.status_label.grid(row=4, column=0, padx=20, pady=5, sticky="ew")


    def is_admin(self):
        """Check if the script is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def get_available_drives(self):
        """Get a list of non-system drives."""
        drives = []
        system_drive = os.getenv('SystemDrive', 'C:').upper()
        for part in psutil.disk_partitions():
            if part.fstype and 'rw' in part.opts: # Check if it's a writable partition
                if part.mountpoint.upper() != system_drive.upper():
                    drives.append(part.mountpoint)
        return drives

    def on_drive_select(self, drive):
        """Enable scan button when a valid drive is selected."""
        self.selected_drive = drive
        self.scan_button.configure(state="normal")
        self.status_label.configure(text=f"Drive {drive} selected. Ready to scan.")
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", "end")
        self.results_textbox.configure(state="disabled")
        self.delete_button.configure(state="disabled")

    def update_status(self, message):
        """Thread-safe way to update the status label."""
        self.status_label.configure(text=message)

    def update_results(self, content):
        """Thread-safe way to update the results textbox."""
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", "end")
        self.results_textbox.insert("1.0", content)
        self.results_textbox.configure(state="disabled")
        
    def get_folder_size(self, path):
        """Recursively get folder size, ignoring permission errors."""
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            continue # Skip files we can't access
        except PermissionError:
            self.update_status(f"Warning: Permission denied for parts of {path}. Size may be inaccurate.")
        return total_size

    # --- Threaded Operations ---

    def start_scan_thread(self):
        """Starts the scanning process in a new thread to avoid freezing the GUI."""
        self.scan_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.update_status(f"Scanning {self.selected_drive} for Windows installation... This may take a while.")
        
        thread = threading.Thread(target=self.scan_drive, daemon=True)
        thread.start()

    def scan_drive(self):
        """The actual scanning logic that runs in a thread."""
        drive = self.selected_drive
        self.found_folders = []
        self.found_files = []
        self.total_size_gb = 0.0
        
        # Check for a key Windows folder to confirm it's likely a Windows drive
        if not os.path.exists(os.path.join(drive, "Windows", "System32")):
            self.after(0, self.update_status, f"Error: No Windows installation found on {drive}.")
            self.after(0, self.update_results, f"Scan failed.\nThe drive {drive} does not appear to contain a Windows installation.\nCould not find '{os.path.join(drive, 'Windows', 'System32')}'.")
            self.after(0, self.scan_button.configure, {"state": "normal"})
            return

        # Scan for target folders
        results_text = f"Scan Results for Drive {drive}\n"
        results_text += "--------------------------------\n\n"
        results_text += "Found Folders to be Deleted:\n"
        total_bytes = 0

        for folder in WINDOWS_FOLDERS:
            path = os.path.join(drive, folder)
            self.after(0, self.update_status, f"Scanning: {path}...")
            if os.path.exists(path):
                size_bytes = self.get_folder_size(path)
                if size_bytes > 0:
                    size_gb = size_bytes / (1024**3)
                    total_bytes += size_bytes
                    self.found_folders.append(path)
                    results_text += f"- {path:<40} {size_gb:.2f} GB\n"
        
        results_text += "\nFound Root Files to be Deleted:\n"
        for file in WINDOWS_ROOT_FILES:
             path = os.path.join(drive, file)
             if os.path.exists(path):
                try:
                    size_bytes = os.path.getsize(path)
                    size_gb = size_bytes / (1024**3)
                    total_bytes += size_bytes
                    self.found_files.append(path)
                    results_text += f"- {path:<40} {size_gb:.2f} GB\n"
                except OSError:
                    continue

        self.total_size_gb = total_bytes / (1024**3)
        results_text += "\n--------------------------------\n"
        results_text += f"Total space to be reclaimed: {self.total_size_gb:.2f} GB\n\n"
        
        if not self.found_folders and not self.found_files:
            results_text += "No Windows-related folders or files found."
            self.after(0, self.update_status, f"Scan complete. No Windows files found on {drive}.")
        else:
            results_text += "WARNING: The 'Users' folder will be deleted. Ensure you have backed up all personal data from it."
            self.after(0, self.update_status, "Scan complete. Review the files below before deleting.")
            self.after(0, self.delete_button.configure, {"state": "normal"})

        self.after(0, self.update_results, results_text)
        self.after(0, self.scan_button.configure, {"state": "normal"})

    def start_delete_thread(self):
        """Confirms and starts the deletion process in a thread."""
        if not messagebox.askyesno("FINAL CONFIRMATION",
            f"You are about to permanently delete {self.total_size_gb:.2f} GB of data from drive {self.selected_drive}.\n\n"
            "This includes folders like 'Windows' and 'Users'.\n\n"
            "THIS ACTION CANNOT BE UNDONE. Are you absolutely sure?"):
            return
            
        self.scan_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.drives_menu.configure(state="disabled")

        thread = threading.Thread(target=self.delete_files, daemon=True)
        thread.start()

    def delete_files(self):
        """The actual deletion logic."""
        all_paths = self.found_folders + self.found_files
        for i, path in enumerate(all_paths):
            self.after(0, self.update_status, f"Deleting ({i+1}/{len(all_paths)}): {os.path.basename(path)}...")
            try:
                # Forcing permissions is crucial for system folders
                # 1. Take ownership
                subprocess.run(['takeown', '/F', path, '/R', '/D', 'Y'], check=True, capture_output=True)
                # 2. Grant full control to the current user
                subprocess.run(['icacls', path, '/grant', f'{os.getlogin()}:F', '/T'], check=True, capture_output=True)
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
                
                self.after(0, self.update_status, f"Successfully deleted {os.path.basename(path)}.")

            except (subprocess.CalledProcessError, OSError, PermissionError) as e:
                error_message = f"ERROR: Failed to delete {path}. Reason: {str(e)}. Some files may remain. It's safer to format the drive."
                self.after(0, self.update_status, error_message)
                self.after(0, lambda: messagebox.showerror("Deletion Error", error_message))
                # Re-enable controls after error
                self.after(0, self.scan_button.configure, {"state": "normal"})
                self.after(0, self.drives_menu.configure, {"state": "normal"})
                return # Stop the process

        final_message = f"Deletion process completed on drive {self.selected_drive}. Reclaimed approximately {self.total_size_gb:.2f} GB."
        self.after(0, self.update_status, final_message)
        self.after(0, self.update_results, final_message + "\nYou can now close the program.")
        self.after(0, lambda: messagebox.showinfo("Success", final_message))
        self.after(0, self.drives_menu.configure, {"state": "normal"})


if __name__ == "__main__":
    app = WindowsRemoverApp()
    app.mainloop()