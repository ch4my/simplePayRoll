import tkinter as tk
from tkinter import ttk, messagebox
import auth_database

class AuthWindow(tk.Tk):
    """Main authentication window with login/signup."""
    
    def __init__(self):
        super().__init__()
        self.title("Payroll System - Authentication")
        self.geometry("450x600")
        self.resizable(False, False)
        
        # Store authenticated user data
        self.authenticated_user = None
        
        # Track current view
        self.current_view = "login"  # "login" or "signup"
        
        auth_database.connect_auth()
        self._build_ui()
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _build_ui(self):
        """Build the authentication UI."""
        
        # Header
        header = tk.Frame(self, bg='#2c3e50', height=80)
        header.pack(fill='x')
        tk.Label(header, text="🔐 Payroll System", font=('Arial', 20, 'bold'), 
                 bg='#2c3e50', fg='white').pack(pady=20)
        
        # Container for forms
        self.form_container = tk.Frame(self, bg='white')
        self.form_container.pack(fill='both', expand=True)
        
        # Show login by default
        self._show_login_form()
    
    def _show_login_form(self):
        """Show the login form."""
        # Clear container
        for widget in self.form_container.winfo_children():
            widget.destroy()
        
        self.current_view = "login"
        container = tk.Frame(self.form_container, bg='white')
        container.pack(expand=True, pady=40)
        
        tk.Label(container, text="Welcome Back!", font=('Arial', 18, 'bold'), 
                 bg='white', fg='#2c3e50').pack(pady=(0, 30))
        
        # Username
        tk.Label(container, text="Username:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.login_username = tk.Entry(container, font=('Arial', 12), width=30)
        self.login_username.pack(pady=(5, 15), padx=40, ipady=5)
        
        # Password
        tk.Label(container, text="Password:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.login_password = tk.Entry(container, font=('Arial', 12), width=30, show='●')
        self.login_password.pack(pady=(5, 30), padx=40, ipady=5)
        
        # Login Button
        login_btn = tk.Button(container, text="Login", font=('Arial', 12, 'bold'), 
                             bg='#27ae60', fg='white', width=28, height=2,
                             cursor='hand2', command=self.on_login,
                             relief='flat')
        login_btn.pack(pady=10)
        
        # Divider
        tk.Label(container, text="──────────  OR  ──────────", 
                 bg='white', fg='#7f8c8d', font=('Arial', 9)).pack(pady=20)
        
        # Sign Up Button
        signup_btn = tk.Button(container, text="Create New Account", font=('Arial', 11), 
                              bg='#3498db', fg='white', width=28, height=2,
                              cursor='hand2', command=self._show_signup_form,
                              relief='flat')
        signup_btn.pack()
        
        # Bind Enter key
        self.login_password.bind('<Return>', lambda e: self.on_login())
        self.login_username.focus_set()
    
    def _show_signup_form(self):
        """Show the signup form."""
        # Clear container
        for widget in self.form_container.winfo_children():
            widget.destroy()
        
        self.current_view = "signup"
        container = tk.Frame(self.form_container, bg='white')
        container.pack(expand=True, pady=20)
        
        tk.Label(container, text="Create Account", font=('Arial', 18, 'bold'), 
                 bg='white', fg='#2c3e50').pack(pady=(0, 20))
        
        # Full Name
        tk.Label(container, text="Full Name:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.signup_fullname = tk.Entry(container, font=('Arial', 11), width=30)
        self.signup_fullname.pack(pady=(5, 10), padx=40, ipady=4)
        
        # Email
        tk.Label(container, text="Email:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.signup_email = tk.Entry(container, font=('Arial', 11), width=30)
        self.signup_email.pack(pady=(5, 10), padx=40, ipady=4)
        
        # Username
        tk.Label(container, text="Username:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.signup_username = tk.Entry(container, font=('Arial', 11), width=30)
        self.signup_username.pack(pady=(5, 10), padx=40, ipady=4)
        
        # Password
        tk.Label(container, text="Password (min 6 characters):", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.signup_password = tk.Entry(container, font=('Arial', 11), width=30, show='●')
        self.signup_password.pack(pady=(5, 10), padx=40, ipady=4)
        
        # Confirm Password
        tk.Label(container, text="Confirm Password:", font=('Arial', 10), 
                 bg='white', fg='#34495e').pack(anchor='w', padx=40)
        self.signup_confirm = tk.Entry(container, font=('Arial', 11), width=30, show='●')
        self.signup_confirm.pack(pady=(5, 20), padx=40, ipady=4)
        
        # Signup Button
        signup_btn = tk.Button(container, text="Create Account", font=('Arial', 12, 'bold'), 
                              bg='#3498db', fg='white', width=28, height=2,
                              cursor='hand2', command=self.on_signup,
                              relief='flat')
        signup_btn.pack(pady=10)
        
        # Back to Login Button
        back_btn = tk.Button(container, text="← Back to Login", font=('Arial', 10), 
                            bg='white', fg='#3498db', cursor='hand2',
                            command=self._show_login_form, relief='flat',
                            borderwidth=0)
        back_btn.pack(pady=10)
        
        # Bind Enter key
        self.signup_confirm.bind('<Return>', lambda e: self.on_signup())
        self.signup_fullname.focus_set()
    
    def on_login(self):
        """Handle login button click."""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter username and password.")
            return
        
        success, message, user_data = auth_database.authenticate_user(username, password)
        
        if success:
            self.authenticated_user = user_data
            messagebox.showinfo("Success", f"Welcome, {user_data['full_name'] or user_data['username']}!")
            self.destroy()  # Close auth window and proceed to main app
        else:
            messagebox.showerror("Login Failed", message)
            self.login_password.delete(0, tk.END)
            self.login_username.focus_set()
    
    def on_signup(self):
        """Handle signup button click."""
        full_name = self.signup_fullname.get().strip()
        email = self.signup_email.get().strip()
        username = self.signup_username.get().strip()
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()
        
        if not username or not email or not password:
            messagebox.showwarning("Input Required", "Please fill in all required fields.")
            return
        
        if password != confirm:
            messagebox.showwarning("Password Mismatch", "Passwords do not match.")
            self.signup_confirm.delete(0, tk.END)
            self.signup_confirm.focus_set()
            return
        
        success, message = auth_database.create_user(username, email, password, full_name)
        
        if success:
            messagebox.showinfo("Success", message + "\n\nYou can now login with your credentials.")
            # Switch to login form
            self._show_login_form()
        else:
            messagebox.showerror("Signup Failed", message)
    
    def on_close(self):
        """Handle window close event."""
        auth_database.close_auth_connection()
        self.destroy()

def authenticate() -> dict:
    """
    Show authentication window and return authenticated user data.
    Returns empty dict if authentication was cancelled.
    """
    auth_window = AuthWindow()
    auth_window.mainloop()
    return auth_window.authenticated_user if auth_window.authenticated_user else {}
