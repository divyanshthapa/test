import pandas as pd
import re
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import Trainer, TrainingArguments
from datasets import Dataset

def extract_amount(description):
    match = re.search(r'\b\d+\b', description)
    return float(match.group()) if match else 0.0

def extract_accounts(description, predicted_type):
    debit_account, credit_account = None, None
    if predicted_type == 'Loan Transaction':
        debit_account = "bank"
        credit_account = "loan"
    elif predicted_type == 'Revenue Transaction':
        debit_account = "accounts receivable"
        credit_account = "service income"
    elif predicted_type == 'Business Startup':
        debit_account = "cash"
        credit_account = "capital"
    else:
        debit_account = "cash"
        credit_account = "capital"
    return debit_account, credit_account

def load_data():
    data = {
        'description': [
            'Business started with capital of 100000',
            'Loan taken from bank amounting to 50000',
            'Earned revenue from consulting services of 5000',
            'LLC Formation with capital contribution of 200000',
            'LLC member contributed 50000 in cash'
        ],
        'transaction_type': [
            'Business Startup', 'Loan Transaction', 'Revenue Transaction', 
            'LLC Formation', 'LLC Capital Contribution'
        ],
    }
    return pd.DataFrame(data)

def preprocess_data(df):
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    def tokenize_function(examples):
        return tokenizer(examples['description'], padding="max_length", truncation=True, max_length=128)

    dataset = Dataset.from_pandas(df)
    dataset = dataset.map(tokenize_function, batched=True)
    label_mapping = {label: idx for idx, label in enumerate(df['transaction_type'].unique())}
    dataset = dataset.map(lambda e: {'labels': label_mapping[e['transaction_type']]})
    return dataset, tokenizer

def train_model_with_bert(df):
    dataset, tokenizer = preprocess_data(df)
    train_dataset = dataset.train_test_split(test_size=0.1)['train']
    val_dataset = dataset.train_test_split(test_size=0.1)['test']
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(df['transaction_type'].unique()))
    training_args = TrainingArguments(
        output_dir='./results',
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    trainer.train()
    model.save_pretrained('./transaction_model')
    tokenizer.save_pretrained('./transaction_model')
    print("Model and tokenizer saved.")
    return model, tokenizer

if __name__ == '__main__':
    df = load_data()
    model, tokenizer = train_model_with_bert(df)
