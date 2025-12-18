import tkinter as tk
from tkinter import ttk, messagebox
import method
import currency
from datetime import datetime
import database

class PayrollApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- Application Window ---
        # Initializes the main window and wires up lifecycle hooks
        self.title("Salary Calculator")
        self.geometry("1000x700")
        database.connect()
        self._build_ui()  # Build all UI sections
        try:
            self.entry_name.focus()
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        """
        Build all UI sections of the app:
        - Input Section (employee form)
        - Actions Section (Compute, Delete, Refresh)
        - Table Section (records list)
        - Details Section (pay & deduction breakdowns)
        - Summary Section (selected employee totals)
        """
        frm = tk.Frame(self)
        frm.pack(fill='x', padx=16, pady=8)

        # --- Input Section ---
        # Split inputs into two columns to use horizontal space
        left_fields = [
            ("Name", "name"),
            ("Company ID", "company_id"),
            ("Age", "age"),
            ("Role", "role"),
        ]
        right_fields = [
            ("Department", "department"),
            ("Start Month (YYYY-MM)", "start_month"),
            ("End Month (YYYY-MM)", "end_month"),
            ("Loan", "loan"),
        ]

        self.vars = {}

        left_col = tk.Frame(frm)
        left_col.grid(row=0, column=0, sticky='nw', padx=(0,12))
        right_col = tk.Frame(frm)
        right_col.grid(row=0, column=1, sticky='nw')

        for r, (lbl, key) in enumerate(left_fields):
            tk.Label(left_col, text=lbl + ":").grid(row=r, column=0, sticky='w', pady=4)
            v = tk.StringVar()
            self.vars[key] = v
            entry = tk.Entry(left_col, textvariable=v, width=36)
            entry.grid(row=r, column=1, padx=6, pady=4)
            if key == 'name':
                self.entry_name = entry

        # Build right-side inputs with dropdowns for month ranges
        now = datetime.now()
        years = list(range(now.year - 10, now.year + 6))
        month_options = [f"{y}-{m:02d}" for y in years for m in range(1,13)]

        for r, (lbl, key) in enumerate(right_fields):
            tk.Label(right_col, text=lbl + ":").grid(row=r, column=0, sticky='w', pady=4)
            v = tk.StringVar()
            self.vars[key] = v
            if key in ("start_month", "end_month"):
                cb = ttk.Combobox(right_col, values=month_options, textvariable=v, width=34, state='readonly')
                cb.grid(row=r, column=1, padx=6, pady=4)
                cb.set(f"{now.year}-{now.month:02d}")
            else:
                tk.Entry(right_col, textvariable=v, width=36).grid(row=r, column=1, padx=6, pady=4)

        # Currency input (optional)
        # Ensure the variable exists before binding to combobox
        if 'currency' not in self.vars:
            self.vars['currency'] = tk.StringVar(value='PHP')

        # Populate currency list dynamically from API; fall back to a small list on failure
        try:
            codes = currency.list_currency_codes()
            codes_display = [c.upper() for c in codes]
        except Exception:
            codes_display = ['PHP','USD','EUR','JPY','AUD','GBP']

        curr_combo = ttk.Combobox(
            right_col,
            values=codes_display,
            textvariable=self.vars['currency'],
            width=34,
            state='readonly'
        )
        # Put it on the next row after the right_fields entries
        curr_row = len(right_fields)
        curr_combo.grid(row=curr_row, column=1, padx=6, pady=4)
        # Default to PHP if available, otherwise first in the list
        default_curr = 'PHP' if 'PHP' in curr_combo['values'] else (curr_combo['values'][0] if curr_combo['values'] else 'PHP')
        curr_combo.set(default_curr)
        tk.Label(right_col, text="Currency:").grid(row=curr_row, column=0, sticky='w', pady=4)

        # --- Actions Section ---
        # Controls for computing, deleting, and refreshing records
        btn_frame = tk.Frame(frm)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=8, sticky='w')
        tk.Button(btn_frame, text="Compute & Save", command=self.on_compute, bg='lightgreen').pack(side='left', padx=6)
        tk.Button(btn_frame, text="Delete Record", command=self.on_delete, bg='lightpink').pack(side='left', padx=6)
        tk.Button(btn_frame, text="Refresh", command=self.on_refresh, bg='lightblue').pack(side='left', padx=6)

        # --- Table Section ---
        # Records list showing overall deductions/salary/total
        cols = ('Name','ID','Age','Role','Department','Months','Overall Salary','Overall Deductions','Total Salary')
        table_frame = tk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=16, pady=6)
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=10)
        for c in cols:
            self.tree.heading(c, text=c)
            if c in ('Overall Deductions','Overall Salary','Total Salary'):
                self.tree.column(c, width=120, anchor='center')
            elif c in ('Name','Role','Department'):
                self.tree.column(c, width=140, anchor='center')
            else:
                self.tree.column(c, width=90, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        table_frame.rowconfigure(0, weight=1)
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
        self.summary_labels = {}
        keys = ['Name','ID','Age','Role','Department','Months','Overall Salary','Overall Deductions','Total Salary']
        for i,k in enumerate(keys):
            tk.Label(summary, text=k+':', width=16, anchor='w').grid(row=i, column=0, sticky='w', padx=6, pady=2)
            lbl = tk.Label(summary, text='', anchor='w')
            if k == 'Overall Deductions':
                lbl.configure(fg='red')
            elif k == 'Overall Salary':
                lbl.configure(fg='green')
            elif k == 'Total Salary':
                lbl.configure(fg='blue', font=('TkDefaultFont', 10, 'bold'))
            lbl.grid(row=i, column=1, sticky='w', padx=6, pady=2)
            self.summary_labels[k] = lbl

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self._load_existing()

    def on_compute(self):
        """
        Compute & Save handler:
        - Validates inputs and computes via method.save_record
        - Inserts a new row into the Table Section
        - Updates Summary and Details sections
        """
        data = {k: v.get() for k,v in self.vars.items()}

        # Derive months from start/end month inputs
        def parse_month(s: str):
            s = str(s).strip()
            for fmt in ("%Y-%m", "%m/%Y", "%b %Y", "%B %Y"):
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.year, dt.month
                except Exception:
                    continue
            raise ValueError("Invalid month format. Use YYYY-MM or MM/YYYY.")

        try:
            y1, m1 = parse_month(data.get('start_month', ''))
            y2, m2 = parse_month(data.get('end_month', ''))
            months = (y2 - y1) * 12 + (m2 - m1) + 1
            if months <= 0:
                raise ValueError("End Month must be after or equal to Start Month.")
            data['months'] = months
        except ValueError as e:
            messagebox.showwarning("Month range error", str(e))
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
        item = self.tree.insert('', tk.END, values=(
            record['name'], record['company_id'], record['age'],
            record['role'], record['department'], record['months'],
            f"{record['totalS']:,}", f"{record['totalD']:,}", f"{record['total']:,}"
        ))

        # update summary and detail subtables
        self.summary_labels['Name'].config(text=record['name'])
        self.summary_labels['ID'].config(text=record['company_id'])
        self.summary_labels['Age'].config(text=str(record['age']))
        self.summary_labels['Role'].config(text=record['role'])
        self.summary_labels['Department'].config(text=record['department'])
        self.summary_labels['Months'].config(text=str(record['months']))
        self.summary_labels['Overall Deductions'].config(text=f"{record['totalD']:,}")
        self.summary_labels['Overall Salary'].config(text=f"{record['totalS']:,}")
        self.summary_labels['Total Salary'].config(text=f"{record['total']:,}")

        # Case-insensitive currency check
        if record.get('currency') and str(record['currency']).upper() != 'PHP':
            self.summary_labels['Overall Salary'].config(
                text=f"{record['overall_salary']:,} ({record['overall_salary_php']:,} PHP @ {record['fx_rate']:.4f})"
            )
            self.summary_labels['Total Salary'].config(
                text=f"{record['total']:,} ({record['total_salary_php']:,} PHP @ {record['fx_rate']:.4f})"
            )

        self._populate_detail_tables_from_record(record)

        for v in self.vars.values():
            v.set('')
        try:
            self.entry_name.focus()
        except Exception:
            pass

    def _load_existing(self):
        """
        Table Section: load existing rows from DB and compute
        display columns (payB/payD/total).
        """
        rows = database.fetch_all()
        for r in rows:
            # r: id, name, company_id, age, role, department, months, loan, deduction, overall_salary (monthly net), total_salary (overall net), created_at
            payD = int(r[8]) if r[8] is not None else 0                       # monthly deduction
            monthly_net = int(r[9]) if r[9] is not None else 0                # monthly net
            payB = monthly_net + payD                                         # monthly gross
            total = int(r[10]) if r[10] is not None else monthly_net          # overall net (from DB)
            # Match the defined columns: ('Name','ID','Age','Role','Department','Months','Overall Salary','Overall Deductions','Total Salary')
            self.tree.insert('', tk.END, iid=str(r[0]), values=(
                r[1], r[2], r[3], r[4], r[5], r[6], f"{payB:,}", f"{payD:,}", f"{total:,}"
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
        total = int(db_row[10]) if db_row[10] is not None else (monthly_net * months)

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
            ('Loan', loan),
            ('Total', payD)
        ]

        self._populate_tree(self.pay_tree, pay_components)
        self._populate_tree(self.ded_tree, ded_components)

        # Update Summary Section to reflect selected row values
        self.summary_labels['Name'].config(text=str(db_row[1]))
        self.summary_labels['ID'].config(text=str(db_row[2]))
        self.summary_labels['Age'].config(text=str(db_row[3]))
        self.summary_labels['Role'].config(text=str(db_row[4]))
        self.summary_labels['Department'].config(text=str(db_row[5]))
        self.summary_labels['Months'].config(text=str(months))
        self.summary_labels['Overall Deductions'].config(text=f"{totalD:,}")
        self.summary_labels['Overall Salary'].config(text=f"{totalS:,}")
        self.summary_labels['Total Salary'].config(text=f"{total:,}")

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
            ('Loan', record['loan']),
            ('Total', record['payD'])
        ]
        self._populate_tree(self.pay_tree, pay_components)
        self._populate_tree(self.ded_tree, ded_components)

    def _populate_tree(self, treewidget, rows):
        """
        Details helper: render a breakdown list with optional divider rows.
        """
        for item in treewidget.get_children():
            treewidget.delete(item)
        for comp, amt in rows:
            if comp == '' and amt == '':
                # divider row: a thin separator line with no values
                treewidget.insert('', tk.END, values=('', ''))
            else:
                treewidget.insert('', tk.END, values=(comp, f"{amt:,}"))

if __name__ == "__main__":
    app = PayrollApp()
    app.mainloop()