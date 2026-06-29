# Simple Payroll System

A standalone desktop application built with Python and Tkinter for managing employee data, computing salaries, and tracking monthly deductions and loans. 

## Features

- **Authentication System:** Secure login and account creation utilizing a local SQLite database and password hashing.
- **Employee Management:** Easily add, edit, and delete employee payroll records.
- **Dynamic Computations:** Automatically computes gross pay, total deductions, and net salary based on configurable components (Basic, HRA, Conveyance, Tax, Health Insurance).
- **Currency Conversion:** Integrates with a live REST API to instantly convert PHP salaries into other major currencies (USD, EUR, JPY, AUD, GBP).
- **Exporting Capabilities:** Generate professional reports and export data directly to Excel (`.xlsx`) or PDF formats.
- **Modern Desktop UI:** Built using a custom-themed Tkinter layout for a clean, user-friendly experience.

## Tech Stack

- **Language:** Python
- **GUI Framework:** Tkinter
- **Database:** SQLite (local files: `payroll.db` & `auth.db`)
- **Key Third-Party Libraries:**
  - `openpyxl`: For Excel exports
  - `reportlab`: For generating PDF reports
  - `requests`: For fetching live exchange rates

## How to Run

1. **Prerequisites:** Ensure you have Python installed on your system.
2. **Install Dependencies:** Open your terminal and install the required libraries by running:
   ```bash
   pip install openpyxl reportlab requests
   ```
3. **Run the Application:** Execute the main app file from your terminal:
   ```bash
   python app.py
   ```
   *Note: Do not run `auth_ui.py` directly; `app.py` acts as the main entry point and handles the startup sequence automatically.*
