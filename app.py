from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
import re
import plotly.express as px  # <-- Plotly added here

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        elif filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            df = extract_table_from_text(text)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        summary = generate_summary(df)
        return jsonify({
            'columns': df.columns.tolist(),
            'data': df.head(50).to_dict(orient='records'),
            'summary': summary
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chart', methods=['POST'])  # <-- This is the new route
def chart():
    data = request.json
    df = pd.DataFrame(data['data'])
    fig = px.bar(df, x=data['x'], y=data['y'], title='AI Chart')
    return jsonify(fig.to_dict())

def extract_table_from_text(text):
    lines = text.strip().split('\n')
    rows = []
    for line in lines:
        match = re.match(r'Date: (.*), Category: (.*), Amount: \$([0-9\.]+)', line)
        if match:
            rows.append({
                'Date': match.group(1),
                'Category': match.group(2),
                'Amount': float(match.group(3))
            })
    return pd.DataFrame(rows)

def generate_summary(df):
    summary = {}
    for col in df.select_dtypes(include='number').columns:
        summary[col] = {
            'mean': df[col].mean(),
            'max': df[col].max(),
            'min': df[col].min()
        }
    return summary

if __name__ == '__main__':
    app.run(debug=True)
