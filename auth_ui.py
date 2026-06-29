import tkinter as tk
from tkinter import ttk, messagebox
import auth_database
from theme import THEME, FONTS

class AuthWindow(tk.Tk):
    #********************************
    #Authentication window
    #********************************
    
    def __init__(self):
        super().__init__()
        self.title("Payroll System - Authentication")
        self.geometry("450x650")
        self.resizable(False, False)
        self.configure(bg=THEME['bg'])
        
        #********************************
        #Store user data
        #********************************
        self.authenticated_user = None
        self.current_view = "login"
        
        auth_database.connect_auth()
        self._build_ui()
        

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _build_ui(self):
        #********************************
        #Build authentication UI
        #********************************
        header = tk.Frame(self, bg=THEME['navy'], height=80)
        header.pack(fill='x')
        tk.Label(header, text="Payroll System", font=FONTS['h1'], 
                 bg=THEME['navy'], fg=THEME['text_light']).pack(pady=20)

        self.form_container = tk.Frame(self, bg=THEME['bg'])
        self.form_container.pack(fill='both', expand=True)
        self._show_login_form()
    
    def _show_login_form(self):
        #********************************
        #Show login form
        #********************************
        for widget in self.form_container.winfo_children():
            widget.destroy()
        
        self.current_view = "login"
        container = tk.Frame(self.form_container, bg=THEME['bg'])
        container.pack(expand=True, pady=40)
        
        tk.Label(container, text="Welcome Back!", font=FONTS['h2'], 
             bg=THEME['bg'], fg=THEME['text']).pack(pady=(0, 30))
        
        tk.Label(container, text="Username:", font=FONTS['body'], 
             bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.login_username = tk.Entry(container, font=FONTS['body'], width=30, 
                           bg=THEME['bg'], fg=THEME['text'], 
                           highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.login_username.pack(pady=(5, 15), padx=40, ipady=6)
        
        tk.Label(container, text="Password:", font=FONTS['body'], 
             bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.login_password = tk.Entry(container, font=FONTS['body'], width=30, show='●',
                           bg=THEME['bg'], fg=THEME['text'],
                           highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.login_password.pack(pady=(5, 30), padx=40, ipady=6)
        
        #********************************
        #Login button
        #********************************
        login_btn = tk.Button(container, text="Log In", font=FONTS['button'], 
                     bg=THEME['primary'], fg=THEME['text_light'], width=20, height=2,
                     activebackground=THEME['primary_dark'], activeforeground=THEME['text_light'],
                     cursor='hand2', command=self.on_login,
                     relief='flat', bd=0)
        login_btn.pack(pady=10)
        self._add_hover_effect(login_btn, THEME['primary'], THEME['primary_dark'])
        
        tk.Label(container, text="──────────  OR  ──────────", 
             bg=THEME['bg'], fg=THEME['muted'], font=FONTS['small']).pack(pady=20)
        
        #********************************
        #Signup button
        #********************************
        signup_btn = tk.Button(container, text="Create New Account", font=FONTS['body'], 
                      bg=THEME['muted'], fg=THEME['navy'], width=25, height=2,
                      activebackground=THEME['primary'], activeforeground=THEME['text_light'],
                      cursor='hand2', command=self._show_signup_form,
                      relief='flat', bd=0)
        signup_btn.pack()
        self._add_hover_effect(signup_btn, THEME['muted'], THEME['primary'], fg_hover=THEME['text_light'])
        self.login_password.bind('<Return>', lambda e: self.on_login())
        self.login_username.focus_set()
    
    def _show_signup_form(self):
        for widget in self.form_container.winfo_children():
            widget.destroy()
        
        self.current_view = "signup"
        container = tk.Frame(self.form_container, bg=THEME['bg'])
        container.pack(expand=True, pady=10)
        
        tk.Label(container, text="Create Account", font=FONTS['h2'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(pady=(0, 15))
        
        tk.Label(container, text="Full Name:", font=FONTS['body'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.signup_fullname = tk.Entry(container, font=FONTS['body'], width=30,
                                        bg=THEME['bg'], fg=THEME['text'],
                                        highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.signup_fullname.pack(pady=5, padx=40, ipady=4)

        tk.Label(container, text="Email:", font=FONTS['body'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.signup_email = tk.Entry(container, font=FONTS['body'], width=30,
                                     bg=THEME['bg'], fg=THEME['text'],
                                     highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.signup_email.pack(pady=5, padx=40, ipady=4)
        
        tk.Label(container, text="Username:", font=FONTS['body'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.signup_username = tk.Entry(container, font=FONTS['body'], width=30,
                                        bg=THEME['bg'], fg=THEME['text'],
                                        highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.signup_username.pack(pady=5, padx=40, ipady=4)
        
        tk.Label(container, text="Password (min 6 characters):", font=FONTS['body'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.signup_password = tk.Entry(container, font=FONTS['body'], width=30, show='●',
                                        bg=THEME['bg'], fg=THEME['text'],
                                        highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.signup_password.pack(pady=5, padx=40, ipady=4)
        
        tk.Label(container, text="Confirm Password:", font=FONTS['body'], 
                 bg=THEME['bg'], fg=THEME['text']).pack(anchor='w', padx=40)
        self.signup_confirm = tk.Entry(container, font=FONTS['body'], width=30, show='●',
                                       bg=THEME['bg'], fg=THEME['text'],
                                       highlightthickness=1, highlightbackground=THEME['muted'], bd=0, insertbackground=THEME['text'])
        self.signup_confirm.pack(pady=5, padx=40, ipady=4)

        #********************************
        #Back to login link
        #********************************
        back_link = tk.Label(container, text="Back to Log In", 
                     font=(FONTS['small'][0], FONTS['small'][1], 'underline'),
                     bg=THEME['bg'], fg=THEME['primary'], cursor='hand2')
        back_link.pack(anchor='e', pady=(2, 10), padx=(0, 40))
        back_link.bind('<Button-1>', lambda e: self._show_login_form())
        self._add_link_hover(back_link, THEME['primary'], THEME['primary_dark'])
        
        #********************************
        #Signup button
        #********************************
        signup_btn = tk.Button(container, text="Create Account", font=FONTS['button'], 
                              bg=THEME['primary'], fg=THEME['text_light'], width=23, height=2,
                              activebackground=THEME['primary_dark'], activeforeground=THEME['text_light'],
                              cursor='hand2', command=self.on_signup,
                              relief='flat', bd=0)
        signup_btn.pack(pady=10)
        self._add_hover_effect(signup_btn, THEME['primary'], THEME['primary_dark'])
            
        self.signup_confirm.bind('<Return>', lambda e: self.on_signup())
        self.signup_fullname.focus_set()

    def _add_hover_effect(self, widget, normal_bg, hover_bg, *, fg_hover=None):
        def on_enter(_):
            widget['bg'] = hover_bg
            if fg_hover is not None:
                widget['fg'] = fg_hover
        def on_leave(_):
            widget['bg'] = normal_bg
            if fg_hover is not None:
                widget['fg'] = THEME['text_light'] if normal_bg in (THEME['primary'], THEME['primary_dark']) else (THEME['primary'] if normal_bg == THEME['bg'] else THEME['navy'])
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def _add_link_hover(self, widget, normal_fg, hover_fg):
        def on_enter(_):
            widget['fg'] = hover_fg
        def on_leave(_):
            widget['fg'] = normal_fg
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def on_login(self):
        #********************************
        #Handle login button
        #********************************
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
            messagebox.showerror("Log In Failed", message)
            self.login_password.delete(0, tk.END)
            self.login_username.focus_set()
    
    def on_signup(self):
        #********************************
        #Handle signup button
        #********************************
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
        auth_database.close_auth_connection()
        self.destroy()

def authenticate() -> dict:
    #********************************
    #Show auth window
    #********************************
    auth_window = AuthWindow()
    auth_window.mainloop()
    return auth_window.authenticated_user if auth_window.authenticated_user else {}
