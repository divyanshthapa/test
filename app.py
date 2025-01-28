import os
import re
import random
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Define account presets (add your full account presets here)
account_presets = {
   # Basic Transactions
    "office supplies": ("Office Supplies", "Cash"),
    "capital contribution": ("Capital Account", "Bank"),
    "loan repayment": ("Loan Payable", "Bank"),
    "revenue": ("Revenue", "Accounts Receivable"),
    "purchase": ("Inventory", "Accounts Payable"),
    "bank deposit": ("Cash", "Bank"),
    "salary": ("Salaries Expense", "Cash"),
    
    # Rent, Utilities, Insurance, Taxes, and Interest
    "office rent": ("Rent Expense", "Cash"),
    "utilities payment": ("Utility Expense", "Cash"),
    "insurance payment": ("Insurance Expense", "Cash"),
    "tax payment": ("Income Tax Expense", "Cash"),
    "interest expense": ("Interest Expense", "Cash"),
    
    # Asset-related Transactions
    "asset purchase": ("Asset", "Cash"),
    "asset sale": ("Cash", "Asset"),
    "purchase of fixed assets": ("Fixed Assets", "Bank"),
    "sale of fixed assets": ("Cash", "Fixed Assets"),
    "revaluation of asset": ("Asset", "Revaluation Reserve"),
    "impairment expense": ("Impairment Expense", "Asset"),
    "depreciation expense": ("Depreciation Expense", "Accumulated Depreciation"),
    "gain from asset sale": ("Cash", "Gain on Sale of Asset"),
    "loss from asset sale": ("Loss on Sale of Asset", "Cash"),
    
    # Loan Issuances and Payments
    "loan issuance": ("Cash", "Loan Payable"),
    "loan interest payment": ("Interest Expense", "Cash"),
    "received from loan": ("Cash", "Loan Payable"),
    "received bank loan": ("Cash", "Loan Payable"),
    
    # Payments to Suppliers, Employees, and Others
    "supplier payment": ("Accounts Payable", "Cash"),
    "customer payment": ("Cash", "Accounts Receivable"),
    "stock issuance": ("Cash", "Common Stock"),
    "stock buyback": ("Treasury Stock", "Cash"),
    "dividends declared": ("Retained Earnings", "Dividends Payable"),
    "owner withdrawal": ("Owner's Draw", "Cash"),
    "refund to customer": ("Cash", "Revenue"),
    "refund from supplier": ("Accounts Payable", "Cash"),
    "deposit from customer": ("Cash", "Accounts Receivable"),
    "purchase of inventory": ("Inventory", "Accounts Payable"),
    "inventory sale": ("Accounts Receivable", "Sales Revenue"),
    
    # Miscellaneous Expenses and Income
    "paid for services": ("Service Expense", "Cash"),
    "received donation": ("Cash", "Donations Received"),
    "miscellaneous expense": ("Miscellaneous Expense", "Cash"),
    "payment for legal expenses": ("Legal Expenses", "Cash"),
    "payment for consulting services": ("Consulting Expenses", "Cash"),
    "payment for marketing": ("Marketing Expenses", "Cash"),
    "payment for advertising": ("Advertising Expenses", "Cash"),
    "payment for office supplies": ("Office Supplies", "Cash"),
    "payment for office furniture": ("Office Furniture", "Cash"),
    "payment for software": ("Software Expense", "Cash"),
    "payment for subscription": ("Subscription Expense", "Cash"),
    "payment for training": ("Training Expense", "Cash"),
    "payment for repairs": ("Repairs and Maintenance", "Cash"),
    "payment for travel": ("Travel Expense", "Cash"),
    "payment for meals": ("Meals and Entertainment", "Cash"),
    "payment for shipping": ("Shipping Expense", "Accounts Payable"),
    "payment for utilities": ("Utility Expense", "Cash"),
    "payment for rent": ("Rent Expense", "Cash"),
    "payment for salaries": ("Salaries Expense", "Cash"),
    "payment for taxes": ("Income Tax Expense", "Cash"),
    "payment for insurance": ("Insurance Expense", "Cash"),
    "payment for royalties": ("Royalty Expense", "Cash"),
    "payment for research": ("Research and Development", "Cash"),
    "payment for office cleaning": ("Cleaning Expense", "Cash"),
    "payment for office maintenance": ("Maintenance Expense", "Cash"),
    
    # Payments and Receivables from Customers
    "received payment from customer": ("Cash", "Accounts Receivable"),
    "received payment from loan": ("Cash", "Loan Payable"),
    "received refund from supplier": ("Accounts Payable", "Cash"),
    "received refund from customer": ("Cash", "Revenue"),
    
    # Capital and Financial Activities
    "received capital contribution": ("Cash", "Capital Account"),
    "issued invoice": ("Accounts Receivable", "Revenue"),
    "payment of dividends": ("Dividends Payable", "Cash"),
    "transferred from bank": ("Bank", "Cash"),
    "transferred to bank": ("Cash", "Bank"),
    
    # Tax Refunds and Payments
    "tax refund": ("Cash", "Tax Receivable"),
    "payment of payroll taxes": ("Payroll Tax Expense", "Cash"),
    "payment of property tax": ("Property Tax Expense", "Cash"),
    "payment of sales tax": ("Sales Tax Expense", "Cash"),
    "payment of franchise tax": ("Franchise Tax Expense", "Cash"),
    "payment of VAT": ("VAT Payable", "Cash"),
    
    # Stock Transactions
    "purchase of stocks": ("Investment", "Cash"),
    "sale of stocks": ("Cash", "Investment"),
    
    # Bad Debts and Write-offs
    "charge off bad debts": ("Bad Debt Expense", "Accounts Receivable"),
    "write off uncollectible accounts": ("Bad Debt Expense", "Accounts Receivable"),
    
    # Adjustments and Accruals
    "adjustment to inventory": ("Inventory", "Inventory Shrinkage"),
    "bank charge": ("Bank Charges", "Bank"),
    "bank transfer": ("Bank", "Bank"),
    
    # Other common transactions
    "miscellaneous adjustments": ("Miscellaneous Expense", "Cash"),
    "received payment for royalties": ("Cash", "Royalty Revenue"),
    "payment for franchise": ("Franchise Expense", "Cash"),
    "payment for insurance claims": ("Claims Expense", "Cash"),
    "receipt of grants": ("Cash", "Grants Revenue"),
    
    # International Transactions (Forex, etc.)
    "foreign exchange gain": ("Foreign Exchange Gain", "Cash"),
    "foreign exchange loss": ("Foreign Exchange Loss", "Cash"),
    
    # Finance and Investment Transactions
    "loan repayment principal": ("Loan Payable", "Cash"),
    "interest payment on loan": ("Interest Expense", "Cash"),
    "capital gains": ("Investment Gain", "Cash"),
    "capital losses": ("Investment Loss", "Cash"),
    
    # Purchases and Inventory Adjustments
    "purchase of equipment": ("Equipment", "Cash"),
    "purchase of consumables": ("Consumables", "Cash"),
    "inventory adjustment for shrinkage": ("Inventory Shrinkage", "Inventory"),
    "inventory adjustment for write-off": ("Inventory Write-Off", "Inventory"),
    
    # Audit and Compliance
    "audit fee": ("Audit Expense", "Cash"),
    "compliance fee": ("Compliance Expense", "Cash"),
    
    # Cheques and Bank Transactions
    "cheque deposit": ("Cash", "Bank"),
    "cheque payment": ("Accounts Payable", "Cash"),
    "cheque issued": ("Accounts Payable", "Bank"),
    "cheque received": ("Cash", "Accounts Receivable"),
    "cheque bounce fee": ("Bank Charges", "Bank"),
    "cheque dishonoured": ("Accounts Receivable", "Cash"),
    "bank reconciliation adjustment": ("Bank", "Suspense Account"),
    
    # Bank Guarantees and Letters of Credit
    "bank guarantee fee": ("Bank Charges", "Cash"),
    "letter of credit issuance": ("Letter of Credit", "Cash"),
    "letter of credit settlement": ("Cash", "Letter of Credit"),
    
    # Credit and Debit Transactions
    "credit card payment": ("Credit Card Payable", "Cash"),
    "debit card payment": ("Accounts Payable", "Cash"),
    "credit card chargeback": ("Accounts Receivable", "Credit Card Payable"),
    "refund to credit card": ("Credit Card Payable", "Cash"),
    
    # Electronic Funds Transfers
    "electronic transfer received": ("Cash", "Accounts Receivable"),
    "electronic transfer payment": ("Accounts Payable", "Cash"),
    "wire transfer received": ("Cash", "Accounts Receivable"),
    "wire transfer payment": ("Accounts Payable", "Cash"),
}

# Flask app setup
app = Flask(__name__)
app.secret_key = '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'

# Initialize the GPT-2 model for number extraction
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# File path for the journal
journal_file = 'journal.txt'

# Ensure the journal file exists
if not os.path.exists(journal_file):
    with open(journal_file, 'w') as file:
        file.write("Date | Description | DR Account | CR Account | Amount\n")

# Function to extract numbers using GPT-2 or a simpler approach
def extract_numbers_from_text_gpt2(text):
    inputs = tokenizer.encode(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(inputs, max_length=50, num_return_sequences=1)
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    numbers = re.findall(r'\d+(?:\.\d{1,2})?', generated_text)
    return numbers

# Function to match the transaction description to account preset
def match_transaction_to_preset(description):
    description_lower = description.lower()
    for preset_desc, (dr_account, cr_account) in account_presets.items():
        if preset_desc in description_lower:
            return dr_account, cr_account
    return "Unknown DR account", "Unknown CR account"

# Function to log the transaction in the journal file
def log_transaction_in_journal(description, dr_account, cr_account, amount):
    date = datetime.now().strftime("%Y-%m-%d")
    with open(journal_file, 'a') as file:
        file.write(f"{date} | {description} | {dr_account} | {cr_account} | {amount}\n")

# Function to parse `journal.txt` and extract transaction details
def parse_journal(file_path):
    transactions = []
    if not os.path.exists(file_path):
        return transactions

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) == 5:
                    try:
                        date_str = parts[0].strip()
                        description = parts[1].strip()
                        dr_account = parts[2].strip()
                        cr_account = parts[3].strip()
                        amount = float(parts[4].strip())

                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%B %d, %Y")

                        transactions.append([formatted_date, description, dr_account, cr_account, amount])
                    except ValueError:
                        continue
    return transactions

# Function to create a PDF with the parsed journal entries
def generate_pdf(transactions, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    margin = 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, "Journal Entries Report")

    c.setFont("Helvetica-Bold", 10)
    headers = ["Date", "Description", "DR Account", "CR Account", "Amount"]
    header_positions = [margin, 150, 300, 450, 600]
    for header, position in zip(headers, header_positions):
        c.drawString(position, height - margin * 2, header)

    c.setFont("Helvetica", 10)
    y_position = height - margin * 3
    for transaction in transactions:
        if y_position < margin:
            c.showPage()
            y_position = height - margin * 2
            c.setFont("Helvetica-Bold", 10)
            for header, position in zip(headers, header_positions):
                c.drawString(position, height - margin * 2, header)
            y_position -= margin

        c.setFont("Helvetica", 10)
        c.drawString(header_positions[0], y_position, transaction[0])
        c.drawString(header_positions[1], y_position, transaction[1])
        c.drawString(header_positions[2], y_position, transaction[2])
        c.drawString(header_positions[3], y_position, transaction[3])
        c.drawString(header_positions[4], y_position, f"${transaction[4]:,.2f}")

        y_position -= margin // 2

    c.save()

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash("Please provide a transaction description.", "error")
            return redirect(url_for('index'))

        extracted_numbers = extract_numbers_from_text_gpt2(description)
        amount = extracted_numbers[0] if extracted_numbers else '0.00'
        dr_account, cr_account = match_transaction_to_preset(description)
        log_transaction_in_journal(description, dr_account, cr_account, amount)

        return render_template('index.html', description=description, dr_account=dr_account, cr_account=cr_account, amount=amount)

    return render_template('index.html')

@app.route('/generate-pdf')
def generate_pdf():
    try:
        # Create a new PDF instance
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add sample content
        pdf.cell(200, 10, txt="Transaction Lookup Report", ln=True, align="C")
        pdf.ln(10)  # Add a line break
        pdf.cell(200, 10, txt="Generated on: 2025-01-27", ln=True, align="L")

        # Return the PDF as a response
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=output.pdf'
        return response

    except Exception as e:
        # Log the error and return a 500 response
        return f"An error occurred: {str(e)}", 500
# Main entry point
if __name__ == '__main__':
    app.run(debug=True)