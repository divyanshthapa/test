import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import re
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

MODEL_PATH = './transaction_model'
model, tokenizer = None, None

def load_saved_model(model_filename=MODEL_PATH):
    global model, tokenizer
    try:
        model = BertForSequenceClassification.from_pretrained(model_filename)
        tokenizer = BertTokenizer.from_pretrained(model_filename)
        logging.info(f"Model and tokenizer loaded from {model_filename}.")
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        raise e

def extract_amount(description):
    match = re.search(r'\b\d+\b', description)
    return float(match.group()) if match else 0.0

def extract_accounts(description, predicted_type):
    debit_account, credit_account = None, None
    if 'loan' in description.lower():
        debit_account = "loan"
        credit_account = "bank"
    elif 'revenue' in description.lower() or 'earned' in description.lower():
        debit_account = "accounts receivable"
        credit_account = "service income"
    elif 'capital' in description.lower() or 'startup' in description.lower():
        debit_account = "cash"
        credit_account = "capital"
    elif 'llc' in description.lower():
        debit_account = "cash"
        credit_account = "capital"
    else:
        debit_account = "cash"
        credit_account = "capital"
    return debit_account, credit_account

def predict_transaction_type_with_confidence(description):
    inputs = tokenizer(description, return_tensors='pt', padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = torch.argmax(logits, dim=-1).item()
    label_mapping = {
        0: 'Business Startup',
        1: 'Loan Transaction',
        2: 'Revenue Transaction',
        3: 'LLC Formation',
        4: 'LLC Capital Contribution'
    }
    predicted_type = label_mapping[predicted_class_idx]
    confidence_score = torch.softmax(logits, dim=-1).max().item()
    amount = extract_amount(description)
    debit_account, credit_account = extract_accounts(description, predicted_type)
    return debit_account, credit_account, amount, predicted_type, confidence_score

def save_feedback(description, predicted_type, feedback, correct_type=None):
    feedback_file = 'feedback.csv'
    file_exists = os.path.isfile(feedback_file)
    try:
        logging.debug(f"Saving feedback: {description}, {predicted_type}, {feedback}, {correct_type}")
        with open(feedback_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Description', 'Predicted Type', 'Feedback', 'Correct Type'])
                logging.debug("Header row written to CSV.")
            if feedback == 'incorrect' and correct_type:
                writer.writerow([description, predicted_type, feedback, correct_type])
                logging.debug("Feedback row written: incorrect")
            else:
                writer.writerow([description, predicted_type, feedback, 'N/A'])
                logging.debug("Feedback row written: correct or N/A")
        logging.info(f"Feedback saved for description: {description}")
    except Exception as e:
        logging.error(f"Error saving feedback: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if model is None or tokenizer is None:
        load_saved_model()
    predicted_type = None
    confidence_score = None
    debit_account = None
    credit_account = None
    amount = None
    feedback = None
    correct_type = None
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash("Please provide a description for the transaction.", "error")
            return redirect(url_for('index'))
        debit_account, credit_account, amount, predicted_type, confidence_score = predict_transaction_type_with_confidence(description)
        feedback = request.form.get('feedback')
        correct_type = request.form.get('correct_type', '').strip()
        if feedback:
            if feedback == 'incorrect' and not correct_type:
                flash("Please provide the correct type for the transaction.", "error")
            else:
                save_feedback(description, predicted_type, feedback, correct_type)
                flash("Feedback submitted successfully!", "success")
        return render_template(
            'index.html',
            predicted_type=predicted_type,
            confidence_score=confidence_score,
            debit_account=debit_account,
            credit_account=credit_account,
            amount=amount,
            feedback=feedback,
            correct_type=correct_type
        )
    return render_template('index.html')

if __name__ == '__main__':
    load_saved_model()
    app.run(debug=True)
