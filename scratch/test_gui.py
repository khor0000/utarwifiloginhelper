import tkinter as tk
from tkinter import ttk, messagebox

class UtarLoginWindow:
    def __init__(self, callback):
        self.callback = callback
        self.root = tk.Tk()
        self.root.title("UTARWIFI Login")
        self.root.geometry("400x450")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (400 // 2)
        y = (screen_height // 2) - (450 // 2)
        self.root.geometry(f"400x450+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="white", pady=20)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame, 
            text="Sign in to UTARWIFI.", 
            font=("Segoe UI", 18, "bold"), 
            bg="white", 
            fg="#1a1a1a"
        ).pack()

        # Separator line
        tk.Frame(self.root, height=1, bg="#e0e0e0").pack(fill="x", padx=20)

        # Content area
        content_frame = tk.Frame(self.root, bg="white", padx=40, pady=20)
        content_frame.pack(fill="both", expand=True)

        tk.Label(
            content_frame, 
            text="Please login with UTAR username and password", 
            font=("Segoe UI", 10), 
            bg="white", 
            fg="#666666"
        ).pack(anchor="w", pady=(0, 15))

        # Username Field
        self.user_entry = self.create_styled_entry(content_frame, "Login ID")
        
        # Password Field
        self.pass_entry = self.create_styled_entry(content_frame, "Password", show="*")

        # Login Button
        login_btn = tk.Button(
            content_frame,
            text="Log In",
            font=("Segoe UI", 12, "bold"),
            bg="#204f9e",
            fg="white",
            activebackground="#1a3f7e",
            activeforeground="white",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=self.submit
        )
        login_btn.pack(fill="x", pady=20)

        # Footer
        footer_frame = tk.Frame(self.root, bg="#f9f9f9", height=80)
        footer_frame.pack(fill="x", side="bottom")
        
        # User icon placeholder at bottom (similar to image)
        tk.Label(footer_frame, text="👤", font=("Segoe UI", 24), bg="#f9f9f9", fg="#00a0e9").pack(pady=10)

    def create_styled_entry(self, parent, placeholder, show=None):
        frame = tk.Frame(parent, bg="#f0f0f0", bd=1, highlightthickness=1, highlightbackground="#cccccc", highlightcolor="#204f9e")
        frame.pack(fill="x", pady=8)
        
        entry = tk.Entry(
            frame, 
            font=("Segoe UI", 11), 
            bg="#fdfdfd", 
            relief="flat", 
            show=show,
            insertbackground="#204f9e"
        )
        entry.pack(fill="x", padx=10, pady=8)
        
        # Placeholder text would require more logic, so we'll just use a label above or standard entries
        # For now, let's keep it simple as standard entries
        return entry

    def submit(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Input Error", "Please enter both username and password.")
            return
            
        self.root.destroy()
        self.callback(username, password)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    def my_callback(u, p):
        print(f"Captured: {u} / {p}")
    
    app = UtarLoginWindow(my_callback)
    app.run()
