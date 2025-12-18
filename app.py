import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import method
import currency
import database
import auth_ui
import export

class PayrollApp(tk.Tk):
    def __init__(self, user_data):
        super().__init__()
        # Store authenticated user
        self.current_user = user_data
        
        # --- Application Window ---
        self.title(f"Salary Calculator - {user_data.get('full_name') or user_data['username']}")
        self.geometry("1000x700")
        database.connect()
        self._build_ui()
        try:
            self.entry_name.focus_set()
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Add user info to header
        self._add_user_header()
    
    def _add_user_header(self):
        """Add header showing logged-in user info."""
        header = tk.Frame(self, height=60)
        header.pack(side='top', fill='x', before=self.winfo_children()[0], padx=16, pady=(10,0))
        
        # Username display
        user_label = tk.Label(header, 
                             text=f"User: {self.current_user['username']}",
                             fg='#2c3e50', font=('Arial', 10))
        user_label.pack(side='top', anchor='w')
        
        # Email display
        email_label = tk.Label(header, 
                              text=f"Email: {self.current_user.get('email', '')}",
                              fg='#2c3e50', font=('Arial', 10))
        email_label.pack(side='top', anchor='w')
    
    def on_logout(self):
        """Handle logout action."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            database.close_connection()
            self.destroy()
            # Restart authentication
            main()
    
    def _build_ui(self):
        """
        Build all UI sections of the app:
        - Table Section (records list) with action icons
        - Details Section (pay & deduction breakdowns)
        - Summary Section (selected employee totals)
        """
        # Initialize variables dict (needed for potential future use)
        self.vars = {}
        self.entry_name = None  # No input form

        # --- Table Section ---
        # Records list showing overall deductions/salary/total
        cols = ('Name','ID','Age','Role','Department','Months','Overall Pay','Overall Deductions','Loan','Total Salary','Converted Values')
        table_frame = tk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=16, pady=6)
        
        # --- Header with title, action icons, and Convert Controls ---
        header_frame = tk.Frame(table_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0,8))
        
        # Left side: Title
        tk.Label(header_frame, text="Employee Payroll Data", font=('Arial', 14, 'bold')).pack(side='left')
        
        # Right side: Action icons
        action_frame = tk.Frame(header_frame)
        action_frame.pack(side='right')
        
        # Delete button
        delete_btn = tk.Button(action_frame, text="Delete", font=('Arial', 10), 
                              bg='#e74c3c', fg='white', width=8, height=1,
                              cursor='hand2', command=self.on_delete, relief='flat', padx=10, pady=5)
        delete_btn.pack(side='left', padx=3)
        
        # Refresh button
        refresh_btn = tk.Button(action_frame, text="Refresh", font=('Arial', 10),
                               bg='#3498db', fg='white', width=8, height=1,
                               cursor='hand2', command=self.on_refresh, relief='flat', padx=10, pady=5)
        refresh_btn.pack(side='left', padx=3)
        
        # Add button
        add_btn = tk.Button(action_frame, text="Add", font=('Arial', 10),
                           bg='#27ae60', fg='white', width=8, height=1,
                           cursor='hand2', command=self.on_add_employee, relief='flat', padx=10, pady=5)
        add_btn.pack(side='left', padx=3)
        
        # Convert controls row
        convert_top = tk.Frame(table_frame)
        convert_top.grid(row=1, column=0, columnspan=2, sticky='e', pady=(0,4))
        self.convert_currency_var = tk.StringVar(value='PHP')
        try:
            codes = currency.list_currency_codes()
            codes_display = [c.upper() for c in codes]
        except Exception:
            codes_display = ['PHP','USD','EUR','JPY','AUD','GBP']
        self.convert_combo = ttk.Combobox(convert_top, values=codes_display, textvariable=self.convert_currency_var, width=12, state='readonly')
        self.convert_combo.pack(side='right', padx=6)
        tk.Label(convert_top, text="Convert total salary into:").pack(side='right')
        self.convert_combo.bind('<<ComboboxSelected>>', lambda e: self._update_convert_column())
        
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=9)
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

        # --- Details Section ---
        # Pay and Deduction breakdowns (monthly)
        details_frame = tk.Frame(self)
        details_frame.pack(fill='x', padx=16, pady=(0,10))

        pay_frame = tk.LabelFrame(details_frame, text="Pay Breakdown (Monthly)")
        pay_frame.grid(row=0, column=0, sticky='nsew', padx=(0,8))
        self.pay_tree = ttk.Treeview(pay_frame, columns=('Component','Amount'), show='headings', height=4)
        self.pay_tree.heading('Component', text='Component')
        self.pay_tree.heading('Amount', text='Amount')
        self.pay_tree.column('Component', width=200, anchor='w')
        self.pay_tree.column('Amount', width=120, anchor='e')
        self.pay_tree.pack(fill='both', expand=True)

        ded_frame = tk.LabelFrame(details_frame, text="Deduction Breakdown (Monthly)")
        ded_frame.grid(row=0, column=1, sticky='nsew')
        self.ded_tree = ttk.Treeview(ded_frame, columns=('Component','Amount'), show='headings', height=4)
        self.ded_tree.heading('Component', text='Component')
        self.ded_tree.heading('Amount', text='Amount')
        self.ded_tree.column('Component', width=200, anchor='w')
        self.ded_tree.column('Amount', width=120, anchor='e')
        self.ded_tree.pack(fill='both', expand=True)

        details_frame.columnconfigure(0, weight=1)
        details_frame.columnconfigure(1, weight=1)

        # --- Summary Section ---
        # Selected/just-saved employee totals and metadata
        summary = tk.LabelFrame(self, text="Employee Selected Summary")
        summary.pack(fill='x', padx=16, pady=6)
        sum_inner = tk.Frame(summary)
        sum_inner.pack(fill='both', expand=True, padx=10, pady=10)

        self.summary_labels = {}
        keys = ['Name','ID','Age','Role','Department','Months','Overall Pay','Overall Deductions','Loan','Total Salary']
        sum_inner.columnconfigure(1, weight=1)
        for i,k in enumerate(keys):
            tk.Label(sum_inner, text=k+':', width=16, anchor='w').grid(row=i, column=0, sticky='w', padx=6, pady=2)
            lbl = tk.Label(sum_inner, text='', anchor='w')
            if k == 'Overall Deductions':
                lbl.configure(fg='red')
            elif k == 'Overall Pay':
                lbl.configure(fg='green')
            elif k == 'Total Salary':
                lbl.configure(fg='blue', font=('TkDefaultFont', 10, 'bold'))
            lbl.configure(wraplength=800, justify='left')
            lbl.grid(row=i, column=1, sticky='w', padx=6, pady=2)
            self.summary_labels[k] = lbl

        # --- Bottom Action Buttons ---
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill='x', padx=16, pady=10)
        
        # Export buttons (left side)
        export_frame = tk.Frame(bottom_frame)
        export_frame.pack(side='left')
        
        export_excel_btn = tk.Button(export_frame, text="📊 Export to Excel", 
                                     bg='#27ae60', fg='white',
                                     font=('Arial', 11, 'bold'), cursor='hand2',
                                     command=self.on_export_excel, relief='flat', 
                                     padx=20, pady=10)
        export_excel_btn.pack(side='left', padx=(0, 10))
        
        export_pdf_btn = tk.Button(export_frame, text="📄 Export to PDF", 
                                   bg='#e67e22', fg='white',
                                   font=('Arial', 11, 'bold'), cursor='hand2',
                                   command=self.on_export_pdf, relief='flat', 
                                   padx=20, pady=10)
        export_pdf_btn.pack(side='left')
        
        # Logout button (right side)
        logout_bottom_btn = tk.Button(bottom_frame, text="🚪 Log out", bg='#e74c3c', fg='white',
                                     font=('Arial', 12, 'bold'), cursor='hand2',
                                     command=self.on_logout, relief='flat', 
                                     padx=50, pady=12)
        logout_bottom_btn.pack(side='right')

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self._load_existing()
    
    def on_add_employee(self):
        """Show dialog to add a new employee."""
        self._show_employee_dialog()
    
    def _show_employee_dialog(self, edit_record=None):
        """Show dialog for adding or editing employee."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Payroll Data" if not edit_record else "Edit Payroll Data")
        dialog.geometry("450x600")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # Header
        header = tk.Frame(dialog, bg='#3498db', height=60)
        header.pack(fill='x')
        tk.Label(header, text="Add Payroll Data" if not edit_record else "Edit Payroll Data", 
                font=('Arial', 16, 'bold'), bg='#3498db', fg='white').pack(pady=15)
        
        # Create form
        form_frame = tk.Frame(dialog, padx=30, pady=20)
        form_frame.pack(fill='both', expand=True)
        
        # Generate month options for the next 2 years
        from datetime import datetime, timedelta
        current_date = datetime.now()
        months_options = []
        for i in range(36):  # 3 years of months
            date = datetime(current_date.year, current_date.month, 1) + timedelta(days=32*i)
            date = date.replace(day=1)
            months_options.append(date.strftime('%Y/%m'))
        
        fields = [
            ('Name:', 'name'),
            ('Company ID:', 'company_id'),
            ('Age:', 'age'),
            ('Role:', 'role'),
            ('Department:', 'department'),
            ('Start Date (YYYY/MM):', 'start_date'),
            ('End Date (YYYY/MM):', 'end_date'),
            ('Loan:', 'loan'),
        ]
        
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, anchor='w', font=('Arial', 10)).grid(row=i, column=0, sticky='w', pady=10, padx=(0, 10))
            if key in ('start_date', 'end_date'):
                var = tk.StringVar(value=current_date.strftime('%Y/%m'))
                widget = ttk.Combobox(form_frame, textvariable=var, values=months_options, width=28, font=('Arial', 10), state='readonly')
            else:
                var = tk.StringVar()
                widget = tk.Entry(form_frame, textvariable=var, width=30, font=('Arial', 10))
            widget.grid(row=i, column=1, pady=10, padx=(0, 0), ipady=5)
            entries[key] = var
            
            # Pre-fill if editing
            if edit_record:
                if key == 'start_date' and 'start_month' in edit_record:
                    var.set(edit_record['start_month'])
                elif key == 'end_date' and 'end_month' in edit_record:
                    var.set(edit_record['end_month'])
                elif key in edit_record:
                    var.set(str(edit_record[key]))
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def on_save():
            self.on_compute(entries, dialog)
        
        save_btn = tk.Button(btn_frame, text="Save", bg='#27ae60', fg='white',
                            command=on_save, cursor='hand2', relief='flat', 
                            font=('Arial', 11, 'bold'), padx=30, pady=8)
        save_btn.pack(side='left', padx=8)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", bg='#95a5a6', fg='white',
                              command=dialog.destroy, cursor='hand2', relief='flat', 
                              font=('Arial', 11, 'bold'), padx=30, pady=8)
        cancel_btn.pack(side='left', padx=8)
    
    def on_compute(self, entries=None, dialog=None):
        """
        Compute & Save handler:
        - Validates inputs and computes via method.save_record
        - Inserts a new row into the Table Section
        - Updates Summary and Details sections
        """
        if entries is None:
            # Called from old code path (shouldn't happen now)
            messagebox.showinfo("Info", "Use the Add button to add employees.")
            return
            
        data = {k: v.get() for k,v in entries.items()}
        
        # Calculate months from start and end dates
        try:
            start_date_str = data.get('start_date', '').strip()
            end_date_str = data.get('end_date', '').strip()
            
            if not start_date_str or not end_date_str:
                raise ValueError("Start Date and End Date are required.")
            
            # Parse dates (YYYY-MM format)
            start_parts = start_date_str.split('/')
            end_parts = end_date_str.split('/')
            
            start_year, start_month_num = int(start_parts[0]), int(start_parts[1])
            end_year, end_month_num = int(end_parts[0]), int(end_parts[1])
            
            # Calculate number of months
            months = (end_year - start_year) * 12 + (end_month_num - start_month_num) + 1
            
            if months < 1:
                raise ValueError("End Date must be equal to or after Start Date.")
            
            if months > 12:
                raise ValueError("Period cannot exceed 12 months.")
            
            data['months'] = months
            data['start_month'] = start_date_str
            data['end_month'] = end_date_str
            
        except ValueError as e:
            messagebox.showwarning("Validation error", str(e))
            return
        except Exception as e:
            messagebox.showwarning("Date error", "Invalid date format. Please use YYYY/MM format.")
            return
        try:
            record = method.save_record(data)
        except ValueError as e:
            messagebox.showwarning("Validation error", str(e))
            return
        except Exception as e:
            messagebox.showerror("Save error", str(e))
            return

        # Table Section: insert newly computed record
        months_display = f"{record.get('start_month', '').strip()} - {record.get('end_month', '').strip()} ({record['months']})"
        # Convert Into column: compute from PHP total using selected currency
        conv_code = str(self.convert_currency_var.get()).upper()
        try:
            rate = currency.get_rate('php', conv_code.lower()) if conv_code != 'PHP' else 1.0
        except Exception:
            rate = 1.0
        conv_val = int(round(record['total'] * rate))
        item = self.tree.insert('', tk.END, values=(
            record['name'], record['company_id'], record['age'],
            record['role'], record['department'], months_display,
            f"PHP {record['totalS']:,}", f"PHP {record['totalD']:,}", f"PHP {record['loan']:,}", f"PHP {record['total']:,}", f"{conv_code} {conv_val:,}"
        ))

        # update summary and detail subtables
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

        # Case-insensitive currency check
        # Summary stays in base PHP. No inline conversions.

        self._populate_detail_tables_from_record(record)
        
        # Close dialog if provided
        if dialog:
            dialog.destroy()
        
        messagebox.showinfo("Success", "Employee record saved successfully!")

    def _load_existing(self):
        """
        Table Section: load existing rows from DB and compute
        display columns (payB/payD/total).
        """
        rows = database.fetch_all()
        for r in rows:
            # r: id, name, company_id, age, role, department, months, loan, deduction, overall_salary (monthly net), total_salary (overall net), created_at, start_month, end_month, currency
            payD = int(r[8]) if r[8] is not None else 0                       # monthly deduction (no loan)
            monthly_net = int(r[9]) if r[9] is not None else 0                # monthly net (no loan)
            payB = monthly_net + payD                                         # monthly gross
            total = int(r[10]) if r[10] is not None else monthly_net          # overall net (from DB)
            # Match the defined columns: ('Name','ID','Age','Role','Department','Months','Overall Pay','Overall Deductions','Total Salary')
            # Format: start_month - end_month (number of months)
            start_month = str(r[12] or '').strip()
            end_month = str(r[13] or '').strip()
            months_display = f"{start_month} - {end_month} ({r[6]})" if start_month and end_month else f"{start_month or end_month} ({r[6]})"
            conv_code = str(self.convert_currency_var.get()).upper()
            try:
                rate = currency.get_rate('php', conv_code.lower()) if conv_code != 'PHP' else 1.0
            except Exception:
                rate = 1.0
            conv_val = int(round(total * rate))
            self.tree.insert('', tk.END, iid=str(r[0]), values=(
                r[1], r[2], r[3], r[4], r[5], months_display, f"PHP {payB:,}", f"PHP {payD:,}", f"PHP {int(r[7] or 0):,}", f"PHP {total:,}", f"{conv_code} {conv_val:,}"
            ))

    def on_delete(self):
        """
        Actions Section: delete selected record from the table and DB.
        """
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
                method.delete_record(db_id)
            except Exception as e:
                messagebox.showerror("Delete error", f"Record removed from view but DB delete failed: {e}")

    def on_refresh(self):
        """
        Actions Section: refresh the Table Section from the database.
        """
        # Clear table selection and rows
        try:
            self.tree.selection_set(())
        except Exception:
            pass
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear breakdown tables
        for tw in (self.pay_tree, self.ded_tree):
            for item in tw.get_children():
                tw.delete(item)

        # Reset summary labels
        for lbl in self.summary_labels.values():
            try:
                lbl.config(text='')
            except Exception:
                pass

        # Reload rows from DB
        self._load_existing()

    def on_close(self):
        """
        Application Window: cleanup database connection and close window.
        """
        database.close_connection()
        self.destroy()

    def _on_tree_select(self, event):
        """
        Table Section: when a row is selected, update Details Section
        using the row's loan and stored monthly values to compute breakdown totals.
        """
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        # Fetch full row from DB for accurate loan/deduction/net values
        try:
            db_row = database.fetch_one(int(item_id))
        except Exception:
            db_row = None
        if not db_row:
            return

        loan = int(db_row[7]) if db_row[7] is not None else 0
        months = int(db_row[6]) if db_row[6] is not None else 1
        payD = int(db_row[8]) if db_row[8] is not None else 0                 # monthly deduction
        monthly_net = int(db_row[9]) if db_row[9] is not None else 0          # monthly net
        payB = monthly_net + payD                                             # monthly gross
        totalS = payB * months
        totalD = payD * months
        total = int(db_row[10]) if db_row[10] is not None else (monthly_net * months - loan)

        # Use static components for display; compute totals from the DB row to avoid recompute drift
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

        # Breakdown tables remain in base PHP
        self._populate_tree(self.pay_tree, pay_components, 'PHP')
        self._populate_tree(self.ded_tree, ded_components, 'PHP')

        # Update Summary Section to reflect selected row values
        self.summary_labels['Name'].config(text=str(db_row[1]))
        self.summary_labels['ID'].config(text=str(db_row[2]))
        self.summary_labels['Age'].config(text=str(db_row[3]))
        self.summary_labels['Role'].config(text=str(db_row[4]))
        self.summary_labels['Department'].config(text=str(db_row[5]))
        # Format: start_month - end_month (number of months)
        start_month = str(db_row[12] or '').strip()
        end_month = str(db_row[13] or '').strip()
        months_display = f"{start_month} - {end_month} ({months})" if start_month and end_month else f"{start_month or end_month} ({months})"
        self.summary_labels['Months'].config(text=months_display)
        self.summary_labels['Overall Deductions'].config(text=f"PHP {totalD:,}")
        self.summary_labels['Overall Pay'].config(text=f"PHP {totalS:,}")
        self.summary_labels['Loan'].config(text=f"PHP {loan:,}")
        self.summary_labels['Total Salary'].config(text=f"PHP {total:,}")

    def on_export_excel(self):
        """Export payroll data to Excel file."""
        try:
            # Ask user where to save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"payroll_export_{timestamp}.xlsx"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Save Excel Export"
            )
            
            if not filepath:  # User cancelled
                return
            
            # Perform export
            filename = export.export_to_excel(self.current_user, filepath)
            messagebox.showinfo("Export Successful", 
                              f"Payroll data exported successfully!\n\nSaved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export to Excel:\n{str(e)}")
    
    def on_export_pdf(self):
        """Export payroll data to PDF file."""
        try:
            # Ask user where to save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"payroll_export_{timestamp}.pdf"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Save PDF Export"
            )
            
            if not filepath:  # User cancelled
                return
            
            # Perform export
            filename = export.export_to_pdf(self.current_user, filepath)
            messagebox.showinfo("Export Successful", 
                              f"Payroll data exported successfully!\n\nSaved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export to PDF:\n{str(e)}")
    
    def _populate_detail_tables_from_record(self, record):
        """
        Details Section: populate breakdowns right after compute/save
        using the returned record values.
        """
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
        """
        Details helper: render a breakdown list with optional divider rows.
        """
        try:
            treewidget.tag_configure('totalrow', font=('TkDefaultFont', 10, 'bold'))
        except Exception:
            pass
        for item in treewidget.get_children():
            treewidget.delete(item)
        for comp, amt in rows:
            if comp == '' and amt == '':
                # divider row: a thin separator line with no values
                treewidget.insert('', tk.END, values=('', ''))
            else:
                prefix = (str(cur).upper() + ' ') if cur else ''
                tags = ('totalrow',) if str(comp).lower() == 'total' else ()
                treewidget.insert('', tk.END, values=(comp, f"{prefix}{amt:,}"), tags=tags)

def main():
    """Main entry point with authentication."""
    # Show authentication window
    user_data = auth_ui.authenticate()
    
    # If user authenticated successfully, open main app
    if user_data:
        app = PayrollApp(user_data)
        app.mainloop()
    else:
        print("Authentication cancelled.")

if __name__ == "__main__":
    main()