import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Flask app setup
app = Flask(__name__)
app.secret_key = 'ledger_app_secret_key'

# File path for the journal and ledger
journal_file = 'journal.txt'
ledger_file = 'ledger.txt'
trial_balance_file = 'trial_balance.txt'

# Ensure the journal and ledger files exist
for file in [journal_file, ledger_file, trial_balance_file]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write("")

# Function to parse `journal.txt` and create ledger entries
def create_ledger(journal_path, ledger_path):
    ledger = {}

    with open(journal_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) == 5:
                    try:
                        date, particulars, dr_account, cr_account, amount = [p.strip() for p in parts]
                        amount = float(amount)

                        if dr_account not in ledger:
                            ledger[dr_account] = []
                        if cr_account not in ledger:
                            ledger[cr_account] = []

                        ledger[dr_account].append((date, particulars, "Dr", amount))
                        ledger[cr_account].append((date, particulars, "Cr", amount))
                    except ValueError:
                        continue

    with open(ledger_path, 'w') as file:
        for account, entries in ledger.items():
            for entry in entries:
                file.write(f"{entry[0]} | {entry[1]} | {account} | {entry[2]} | {entry[3]:.2f}\n")

# Function to parse `ledger.txt`
def parse_ledger(file_path):
    ledger_entries = []
    if not os.path.exists(file_path):
        return ledger_entries

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) == 5:
                    date, particulars, account, lf, amount = [p.strip() for p in parts]
                    try:
                        amount = float(amount)
                        ledger_entries.append((date, particulars, account, lf, amount))
                    except ValueError:
                        continue
    return ledger_entries

# Function to generate a trial balance
def generate_trial_balance(ledger_path, trial_balance_path):
    trial_balance = {}

    with open(ledger_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) == 5:
                    _, _, account, lf, amount = [p.strip() for p in parts]
                    amount = float(amount)

                    if account not in trial_balance:
                        trial_balance[account] = {"Debit": 0, "Credit": 0}

                    if lf == "Dr":
                        trial_balance[account]["Debit"] += amount
                    elif lf == "Cr":
                        trial_balance[account]["Credit"] += amount

    with open(trial_balance_path, 'w') as file:
        for account, balances in trial_balance.items():
            file.write(f"{account} | {balances['Debit']:.2f} | {balances['Credit']:.2f}\n")

# Function to generate a PDF for the trial balance
def generate_trial_balance_pdf(trial_balance_path, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    margin = 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, "Trial Balance Report")

    c.setFont("Helvetica-Bold", 10)
    headers = ["S/N", "Heads of Accounting", "Debit Balance", "Credit Balance"]
    header_positions = [margin, 100, 300, 450]
    for header, position in zip(headers, header_positions):
        c.drawString(position, height - margin * 2, header)

    c.setFont("Helvetica", 10)
    y_position = height - margin * 3

    with open(trial_balance_path, 'r') as file:
        for i, line in enumerate(file, start=1):
            if y_position < margin:
                c.showPage()
                y_position = height - margin * 2
                c.setFont("Helvetica-Bold", 10)
                for header, position in zip(headers, header_positions):
                    c.drawString(position, height - margin * 2, header)
                y_position -= margin

            c.setFont("Helvetica", 10)
            parts = line.strip().split('|')
            if len(parts) == 3:
                account, debit, credit = [p.strip() for p in parts]
                c.drawString(header_positions[0], y_position, str(i))  # S/N
                c.drawString(header_positions[1], y_position, account)  # Heads of Accounting
                c.drawString(header_positions[2], y_position, f"${debit}")  # Debit Balance
                c.drawString(header_positions[3], y_position, f"${credit}")  # Credit Balance

            y_position -= margin // 2

    c.save()

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Generate ledger from journal
        create_ledger(journal_file, ledger_file)
        generate_trial_balance(ledger_file, trial_balance_file)
        flash("Ledger and Trial Balance successfully updated!", "success")
        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/generate-pdf')
def download_pdf():
    try:
        entries = parse_ledger(ledger_file)
        output_pdf_path = "ledger_report.pdf"
        generate_ledger_pdf(entries, output_pdf_path)
        return send_file(output_pdf_path, as_attachment=True)
    except Exception as e:
        flash(f"Error generating PDF: {e}", "error")
        return redirect(url_for('index'))

@app.route('/generate-trial-balance-pdf')
def download_trial_balance_pdf():
    try:
        output_pdf_path = "trial_balance_report.pdf"
        generate_trial_balance_pdf(trial_balance_file, output_pdf_path)
        return send_file(output_pdf_path, as_attachment=True)
    except Exception as e:
        flash(f"Error generating Trial Balance PDF: {e}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
