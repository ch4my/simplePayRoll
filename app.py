import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from theme import THEME, FONTS
from datetime import datetime
import method
import currency
import database
import auth_ui
import export

class PayrollApp(tk.Tk):
    def __init__(self, user_data):
        super().__init__()
        # ********************************
        # Store user data
        # ********************************
        self.current_user = user_data
        
        self.title(f"Salary Calculator - {user_data.get('full_name') or user_data['username']}")
        self.geometry("1000x700")
        self.configure(bg=THEME['bg'])
        database.connect()
        self._build_ui()
        try:
            self.entry_name.focus_set()
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._add_user_header()
    
    def _add_user_header(self):
        # ********************************
        # Display user info & Header Toolbar
        # ********************************
        header = tk.Frame(self, height=60, bg=THEME['navy'])
        header.pack(side='top', fill='x', before=self.winfo_children()[0])
        
        inner_header = tk.Frame(header, bg=THEME['navy'])
        inner_header.pack(fill='x', padx=20, pady=10)
        
        user_info = tk.Frame(inner_header, bg=THEME['navy'])
        user_info.pack(side='left')
        
        tk.Label(user_info, text="PAYROLL SYSTEM", font=FONTS['h2'], bg=THEME['navy'], fg=THEME['text_light']).pack(side='left', padx=(0, 20))
        
        tk.Label(user_info, 
                             text=f"User: {self.current_user['username']}  |  Email: {self.current_user.get('email', '')}",
                             fg=THEME['text_light'], bg=THEME['navy'], font=FONTS['body']).pack(side='left')

        logout_btn = tk.Button(inner_header, text="Logout", font=FONTS['button'],
                               bg=THEME['muted'], fg=THEME['navy'], cursor='hand2',
                               command=self.on_logout, relief='flat', bd=0, padx=15, pady=5)
        logout_btn.pack(side='right')
    
    def on_logout(self):
        # ********************************
        # Logout user
        # ********************************
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            database.close_connection()
            self.destroy()
            # ********************************
            # Restart auth
            # ********************************
            main()
    
    def _build_ui(self):
        # ********************************
        # Build UI sections/Initialize variables
        # ********************************
        self.vars = {}
        self.entry_name = None

        # ********************************
        # Table Section/Employee records table
        # ********************************
        cols = ('Name','ID','Age','Role','Department','Months','Overall Pay','Overall Deductions','Loan','Total Salary','Converted Values')
        table_frame = tk.Frame(self, bg=THEME['bg'])
        table_frame.pack(fill='both', expand=True, padx=16, pady=6)
        
        # ********************************
        # Header and controls
        # ********************************
        header_frame = tk.Frame(table_frame, bg=THEME['bg'])
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0,8))
        
        # ********************************
        # Title
        # ********************************
        tk.Label(header_frame, text="Employee Payroll Data", font=('Arial', 14, 'bold'), bg=THEME['bg'], fg=THEME['text']).pack(side='left')
        
        # ********************************
        # Action buttons (Toolbar)
        # ********************************
        action_frame = tk.Frame(header_frame, bg=THEME['bg'])
        action_frame.pack(side='right')
        
        export_excel_btn = tk.Button(action_frame, text="Export Excel", font=FONTS['body_bold'],
                         bg=THEME['primary'], fg=THEME['text_light'], width=12,
                         activebackground=THEME['navy'], activeforeground=THEME['text_light'],
                         cursor='hand2', command=self.on_export_excel, relief='flat', bd=0, padx=10, pady=5)
        export_excel_btn.pack(side='left', padx=3)

        export_pdf_btn = tk.Button(action_frame, text="Export PDF", font=FONTS['body_bold'],
                       bg=THEME['primary_dark'], fg=THEME['text_light'], width=12,
                       activebackground=THEME['navy'], activeforeground=THEME['text_light'],
                       cursor='hand2', command=self.on_export_pdf, relief='flat', bd=0, padx=10, pady=5)
        export_pdf_btn.pack(side='left', padx=(3, 15))

        # Vertical separator
        tk.Frame(action_frame, bg=THEME['muted'], width=1, height=20).pack(side='left', padx=5, pady=5)

        delete_btn = tk.Button(action_frame, text="Delete", font=FONTS['body_bold'], 
                  bg='#f54242', fg=THEME['text_light'], width=8,
                  activebackground=THEME['navy'], activeforeground=THEME['text_light'],
                  cursor='hand2', command=self.on_delete, relief='flat', bd=0, padx=10, pady=5)
        delete_btn.pack(side='left', padx=3)
        
        refresh_btn = tk.Button(action_frame, text="Refresh", font=FONTS['body_bold'],
                       bg='#4c80ba', fg=THEME['text_light'], width=8,
                       activebackground=THEME['primary'], activeforeground=THEME['text_light'],
                       cursor='hand2', command=self.on_refresh, relief='flat', bd=0, padx=10, pady=5)
        refresh_btn.pack(side='left', padx=3)
        
        add_btn = tk.Button(action_frame, text="Add", font=FONTS['body_bold'],
                   bg='#5bc763', fg=THEME['text_light'], width=8,
                   activebackground=THEME['primary_dark'], activeforeground=THEME['text_light'],
                   cursor='hand2', command=self.on_add_employee, relief='flat', bd=0, padx=10, pady=5)
        add_btn.pack(side='left', padx=3)
        
        # ********************************
        # Convert currency
        # ********************************
        convert_top = tk.Frame(table_frame, bg=THEME['bg'])
        convert_top.grid(row=1, column=0, columnspan=2, sticky='e', pady=(0,4))
        self.convert_currency_var = tk.StringVar(value='PHP')
        try:
            codes = currency.list_currency_codes()
            codes_display = [c.upper() for c in codes]
        except Exception:
            codes_display = ['PHP','USD','EUR','JPY','AUD','GBP']
        self.convert_combo = ttk.Combobox(convert_top, values=codes_display, textvariable=self.convert_currency_var, width=12, state='readonly')
        self.convert_combo.pack(side='right', padx=6)
        tk.Label(convert_top, text="Convert total salary into:", bg=THEME['bg'], fg=THEME['text']).pack(side='right')
        self.convert_combo.bind('<<ComboboxSelected>>', lambda e: self._update_convert_column())
        
        # ********************************
        # Table styling
        # ********************************
        style = ttk.Style(self)
        style.theme_use('default')  # Use default theme as base to allow color overrides
        style.configure('Treeview',
                    background='#FFFFFF',
                    foreground=THEME['text'],
                    fieldbackground='#FFFFFF',
                    rowheight=26,
                    borderwidth=0,
                    font=FONTS['body'])
        style.map('Treeview', background=[('selected', THEME['muted'])], foreground=[('selected', THEME['navy'])])
        style.configure('Treeview.Heading',
                    background=THEME['navy'],
                    foreground=THEME['text_light'],
                    padding=(6, 6),
                    borderwidth=0,
                    font=FONTS['body_bold'])
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=8, style='Treeview')
        for c in cols:
            self.tree.heading(c, text=c)
            if c in ('Overall Deductions','Overall Pay','Total Salary','Convert Into','Loan'):
                self.tree.column(c, width=120, anchor='center')
            elif c in ('Name','Role','Department'):
                self.tree.column(c, width=120, anchor='center')
            elif c in ('Months'):
                self.tree.column(c, width=150, anchor='center')
            else:
                self.tree.column(c, width=90, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=2, column=0, sticky='nsew')
        vsb.grid(row=2, column=1, sticky='ns')
        table_frame.rowconfigure(2, weight=1, minsize=150)
        table_frame.columnconfigure(0, weight=1)

        # ********************************
        # Details Section
        # ********************************
        details_frame = tk.Frame(self, bg=THEME['bg'])
        details_frame.pack(fill='x', padx=16, pady=(0,10))

        pay_frame = tk.LabelFrame(details_frame, text="Pay Breakdown (Monthly)", bg=THEME['bg'], fg=THEME['text'])
        pay_frame.grid(row=0, column=0, sticky='nsew', padx=(0,8))
        self.pay_tree = ttk.Treeview(pay_frame, columns=('Component','Amount'), show='headings', height=4)
        self.pay_tree.heading('Component', text='Component')
        self.pay_tree.heading('Amount', text='Amount')
        self.pay_tree.column('Component', width=200, anchor='w')
        self.pay_tree.column('Amount', width=120, anchor='e')
        self.pay_tree.pack(fill='both', expand=True)

        ded_frame = tk.LabelFrame(details_frame, text="Deduction Breakdown (Monthly)", bg=THEME['bg'], fg=THEME['text'])
        ded_frame.grid(row=0, column=1, sticky='nsew')
        self.ded_tree = ttk.Treeview(ded_frame, columns=('Component','Amount'), show='headings', height=4)
        self.ded_tree.heading('Component', text='Component')
        self.ded_tree.heading('Amount', text='Amount')
        self.ded_tree.column('Component', width=200, anchor='w')
        self.ded_tree.column('Amount', width=120, anchor='e')
        self.ded_tree.pack(fill='both', expand=True)

        details_frame.columnconfigure(0, weight=1)
        details_frame.columnconfigure(1, weight=1)

        # ********************************
        # Summary Section
        # ********************************
        summary = tk.LabelFrame(self, text="Employee Selected Summary", bg=THEME['bg'], fg=THEME['text'], font=FONTS['body_bold'])
        summary.pack(fill='x', padx=16, pady=6)
        sum_inner = tk.Frame(summary, bg=THEME['bg'])
        sum_inner.pack(fill='both', expand=True, padx=10, pady=10)

        self.summary_labels = {}
        keys = ['Name','ID','Age','Role','Department','Months','Overall Pay','Overall Deductions','Loan','Total Salary']
        
        # Configure 4 columns: label1, value1, label2, value2
        sum_inner.columnconfigure(1, weight=1)
        sum_inner.columnconfigure(3, weight=1)
        
        for i, k in enumerate(keys):
            row = i % 5
            col_offset = (i // 5) * 2
            tk.Label(sum_inner, text=k+':', width=16, anchor='w', font=FONTS['body'], bg=THEME['bg'], fg=THEME['navy']).grid(row=row, column=col_offset, sticky='w', padx=6, pady=4)
            lbl = tk.Label(sum_inner, text='', anchor='w', font=FONTS['body_bold'], bg=THEME['bg'], fg=THEME['text'])
            if k == 'Overall Deductions':
                lbl.configure(fg='#f54242')
            elif k == 'Overall Pay':
                lbl.configure(fg='#5bc763')
            elif k == 'Total Salary':
                lbl.configure(fg=THEME['primary'], font=FONTS['h3'])
            lbl.configure(wraplength=400, justify='left')
            lbl.grid(row=row, column=col_offset+1, sticky='w', padx=6, pady=4)
            self.summary_labels[k] = lbl

        bottom_frame = tk.Frame(self, bg=THEME['bg'])
        bottom_frame.pack(fill='x', padx=16, pady=10)
        
        # ********************************
        # Export buttons are now moved
        # ********************************

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self._load_existing()
    
    def on_add_employee(self):
        # ********************************
        # Add employee
        # ********************************
        self._show_employee_dialog()
    
    def _show_employee_dialog(self, edit_record=None):
        dialog = tk.Toplevel(self)
        dialog.title("Add Payroll Data" if not edit_record else "Edit Payroll Data")
        dialog.geometry("700x450")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg=THEME['navy'], height=60)
        header.pack(fill='x')
        tk.Label(header, text="Add Payroll Data" if not edit_record else "Edit Payroll Data", 
            font=FONTS['h2'], bg=THEME['navy'], fg=THEME['text_light']).pack(pady=15)
        form_frame = tk.Frame(dialog, padx=30, pady=20, bg=THEME['bg'])
        form_frame.pack(fill='both', expand=True)
        
        from datetime import datetime, timedelta
        current_date = datetime.now()
        months_options = []
        for i in range(36):  # 3 years of months
            date = datetime(current_date.year, current_date.month, 1) + timedelta(days=32*i)
            date = date.replace(day=1)
            months_options.append(date.strftime('%Y/%m'))
        
        # ********************************
        # Form layout
        # ********************************
        fields = [
            ('Name:', 'name'),
            ('Company ID:', 'company_id'),
            ('Age:', 'age'),
            ('Role:', 'role'),
            ('Department:', 'department'),
            ('Loan:', 'loan'),
            ('Start Date (YYYY/MM):', 'start_date'),
            ('End Date (YYYY/MM):', 'end_date'),
        ]
        
        entries = {}
        for i, (label, key) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(form_frame, text=label, anchor='w', font=FONTS['body'], bg=THEME['bg'], fg=THEME['navy']).grid(row=row, column=col, sticky='w', pady=15, padx=(0, 10))
            if key in ('start_date', 'end_date'):
                var = tk.StringVar(value=current_date.strftime('%Y/%m'))
                widget = ttk.Combobox(form_frame, textvariable=var, values=months_options, width=22, font=FONTS['body'], state='readonly')
                widget.grid(row=row, column=col+1, pady=15, padx=(0, 30))
            else:
                var = tk.StringVar()
                widget = tk.Entry(form_frame, textvariable=var, width=24, font=FONTS['body'], highlightthickness=1, highlightbackground=THEME['muted'], bd=0)
                widget.grid(row=row, column=col+1, pady=15, padx=(0, 30), ipady=5)
            
            entries[key] = var

            if edit_record:
                if key == 'start_date' and 'start_month' in edit_record:
                    var.set(edit_record['start_month'])
                elif key == 'end_date' and 'end_month' in edit_record:
                    var.set(edit_record['end_month'])
                elif key in edit_record:
                    var.set(str(edit_record[key]))
        
        btn_frame = tk.Frame(dialog, bg=THEME['bg'])
        btn_frame.pack(pady=20)
        
        def on_save():
            self.on_compute(entries, dialog)
        
        save_btn = tk.Button(btn_frame, text="Save", bg=THEME['primary'], fg=THEME['text_light'],
                    command=on_save, cursor='hand2', relief='flat', bd=0,
                            font=FONTS['button'], padx=30, pady=8)
        save_btn.pack(side='left', padx=8)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", bg=THEME['muted'], fg=THEME['navy'],
                      command=dialog.destroy, cursor='hand2', relief='flat', bd=0,
                              font=FONTS['button'], padx=30, pady=8)
        cancel_btn.pack(side='left', padx=8)
    
    def on_compute(self, entries=None, dialog=None):
        # ********************************
        # Compute save record
        # ********************************
        if entries is None:
            messagebox.showinfo("Info", "Use the Add button to add employees.")
            return
            
        data = {k: v.get() for k,v in entries.items()}
        
        # ********************************
        # Calculate months
        # ********************************
        try:
            start_date_str = data.get('start_date', '').strip()
            end_date_str = data.get('end_date', '').strip()
            months, _, _ = method.validate_and_parse_dates(start_date_str, end_date_str)
            data['months'] = months
            data['start_month'] = start_date_str
            data['end_month'] = end_date_str
        except ValueError as e:
            messagebox.showwarning("Validation error", str(e))
            return
        try:
            record = method.compute_record(data)
            record_id = database.insert_salary(record, self.current_user['id'])
            record['id'] = record_id
        except ValueError as e:
            messagebox.showwarning("Validation error", str(e))
            return
        except Exception as e:
            messagebox.showerror("Save error", str(e))
            return

        months_display = f"{record.get('start_month', '').strip()} - {record.get('end_month', '').strip()} ({record['months']})"
        # ********************************
        # Currency conversion
        # ********************************
        conv_code = str(self.convert_currency_var.get()).upper()
        try:
            rate = currency.get_rate('php', conv_code.lower()) if conv_code != 'PHP' else 1.0
        except Exception:
            rate = 1.0
        conv_val = int(round(record['total'] * rate))
        item = self.tree.insert('', tk.END, iid=str(record['id']), values=(
            record['name'], record['company_id'], record['age'],
            record['role'], record['department'], months_display,
            f"PHP {record['totalS']:,}", f"PHP {record['totalD']:,}", f"PHP {record['loan']:,}", f"PHP {record['total']:,}", f"{conv_code} {conv_val:,}"
        ))

        # ********************************
        # Update summary
        # ********************************
        self.summary_labels['Name'].config(text=record['name'])
        self.summary_labels['ID'].config(text=record['company_id'])
        self.summary_labels['Age'].config(text=str(record['age']))
        self.summary_labels['Role'].config(text=record['role'])
        self.summary_labels['Department'].config(text=record['department'])
        self.summary_labels['Months'].config(text=months_display)
        self.summary_labels['Overall Deductions'].config(text=f"PHP {record['totalD']:,}")
        self.summary_labels['Overall Pay'].config(text=f"PHP {record['totalS']:,}")
        self.summary_labels['Loan'].config(text=f"PHP {record['loan']:,}")
        self.summary_labels['Total Salary'].config(text=f"PHP {record['total']:,}")
        self._populate_detail_tables_from_record(record)
        
        if dialog:
            dialog.destroy()
        
        messagebox.showinfo("Success", "Employee record saved successfully!")

    def _load_existing(self):
        conv_code = str(self.convert_currency_var.get()).upper()
        formatted_rows = database.load_and_format_records(conv_code, self.current_user['id'])
        for row_data in formatted_rows:
            record_id = row_data[0]
            display_values = row_data[1:]  # (name, id, age, role, dept, months, payB, payD, loan, total, converted)
            self.tree.insert('', tk.END, iid=str(record_id), values=display_values)

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection error", "Please select a row to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected record?"):
            return

        iid = sel[0]
        try:
            db_id = int(iid)
        except Exception:
            db_id = None

        for item in sel:
            self.tree.delete(item)

        if db_id is not None:
            try:
                database.delete_data(db_id, self.current_user['id'])
            except Exception as e:
                messagebox.showerror("Delete error", f"Record removed from view but DB delete failed: {e}")

    def on_refresh(self):
        # ********************************
        # Refresh table
        # ********************************
        try:
            self.tree.selection_set(())
        except Exception:
            pass
        for item in self.tree.get_children():
            self.tree.delete(item)

        for tw in (self.pay_tree, self.ded_tree):
            for item in tw.get_children():
                tw.delete(item)

        for lbl in self.summary_labels.values():
            try:
                lbl.config(text='')
            except Exception:
                pass

        self._load_existing()

    def on_close(self):
        database.close_connection()
        self.destroy()

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        try:
            db_row = database.fetch_one(int(item_id), self.current_user['id'])
        except Exception:
            db_row = None
        if not db_row:
            return

        # ********************************
        # Compute salary totals
        # ********************************
        totals = method.compute_selected_totals(db_row)
        loan = totals['loan']
        months = totals['months']
        payD = totals['payD']
        payB = totals['payB']
        totalS = totals['totalS']
        totalD = totals['totalD']
        total = totals['total']

        # ********************************
        # Pay components
        # ********************************
        pay_components = [
            ('Salary', method.BASIC),
            ('HRA', method.HRA),
            ('Conveyance', method.CONVEYANCE),
            ('Total', payB)
        ]
        ded_components = [
            ('Tax', method.TAX),
            ('Health Insurance', method.HEALTH_INSURANCE),
            ('Total', payD)
        ]

        self._populate_tree(self.pay_tree, pay_components, 'PHP')
        self._populate_tree(self.ded_tree, ded_components, 'PHP')

        self.summary_labels['Name'].config(text=str(db_row[1]))
        self.summary_labels['ID'].config(text=str(db_row[2]))
        self.summary_labels['Age'].config(text=str(db_row[3]))
        self.summary_labels['Role'].config(text=str(db_row[4]))
        self.summary_labels['Department'].config(text=str(db_row[5]))
        # ********************************
        # Format month display
        # ********************************
        start_month = str(db_row[12] or '').strip()
        end_month = str(db_row[13] or '').strip()
        months_display = f"{start_month} - {end_month} ({months})" if start_month and end_month else f"{start_month or end_month} ({months})"
        self.summary_labels['Months'].config(text=months_display)
        self.summary_labels['Overall Deductions'].config(text=f"PHP {totalD:,}")
        self.summary_labels['Overall Pay'].config(text=f"PHP {totalS:,}")
        self.summary_labels['Loan'].config(text=f"PHP {loan:,}")
        self.summary_labels['Total Salary'].config(text=f"PHP {total:,}")

    def on_export_excel(self):
        # ********************************
        # Export to Excel
        # ********************************
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"payroll_export_{timestamp}.xlsx"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Save Excel Export"
            )
            if not filepath:
                return
            filename = export.export_to_excel(self.current_user, filepath, self.convert_currency_var.get())
            messagebox.showinfo("Export Successful", 
                              f"Payroll data exported successfully!\n\nSaved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export to Excel:\n{str(e)}")
    
    def on_export_pdf(self):
        # ********************************
        # Export to PDF
        # ********************************
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"payroll_export_{timestamp}.pdf"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Save PDF Export"
            )
            if not filepath:
                return
            filename = export.export_to_pdf(self.current_user, filepath, self.convert_currency_var.get())
            messagebox.showinfo("Export Successful", 
                              f"Payroll data exported successfully!\n\nSaved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export to PDF:\n{str(e)}")
    
    def _populate_detail_tables_from_record(self, record):
        pay_components = [
            ('Salary', method.BASIC),
            ('HRA', method.HRA),
            ('Conveyance', method.CONVEYANCE),
            ('Total', record['payB'])
        ]
        ded_components = [
            ('Tax', method.TAX),
            ('Health Insurance', method.HEALTH_INSURANCE),
            ('Total', record['payD'])
        ]
        self._populate_tree(self.pay_tree, pay_components, 'PHP')
        self._populate_tree(self.ded_tree, ded_components, 'PHP')

    def _populate_tree(self, treewidget, rows, cur: str | None = None):
        try:
            treewidget.tag_configure('totalrow', font=('TkDefaultFont', 10, 'bold'))
        except Exception:
            pass
        for item in treewidget.get_children():
            treewidget.delete(item)
        for comp, amt in rows:
            if comp == '' and amt == '':
                treewidget.insert('', tk.END, values=('', ''))
            else:
                prefix = (str(cur).upper() + ' ') if cur else ''
                tags = ('totalrow',) if str(comp).lower() == 'total' else ()
                treewidget.insert('', tk.END, values=(comp, f"{prefix}{amt:,}"), tags=tags)

    def _update_convert_column(self):
        conv_code = str(self.convert_currency_var.get()).upper()
        try:
            rate = currency.get_rate('php', conv_code.lower()) if conv_code != 'PHP' else 1.0
        except Exception:
            rate = 1.0
        for iid in self.tree.get_children():
            vals = list(self.tree.item(iid, 'values'))
            if len(vals) < 11:
                continue
            total_text = str(vals[9])
            try:
                base_total = int(total_text.replace('PHP', '').replace('₱', '').replace(',', '').strip())
            except Exception:
                continue
            converted = int(round(base_total * rate))
            vals[10] = f"{conv_code} {converted:,}"
            self.tree.item(iid, values=vals)

def main():
    # ********************************
    # Main entry point
    # ********************************
    user_data = auth_ui.authenticate()
    
    # ********************************
    # Open main app
    # ********************************
    if user_data:
        app = PayrollApp(user_data)
        app.mainloop()
    else:
        print("Authentication cancelled.")

if __name__ == "__main__":
    main()