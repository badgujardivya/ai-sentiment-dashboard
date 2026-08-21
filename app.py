from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import pandas as pd
import os
import uuid
import json
from datetime import datetime
from model import SentimentAnalyzer
import joblib
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import base64

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MODEL_FOLDER'] = 'static/models'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)

# Global storage for analysis results
analysis_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = str(uuid.uuid4()) + '.csv'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Initialize analyzer
            analyzer = SentimentAnalyzer()
            try:
                results = analyzer.analyze_dataset(filepath)
                session['analysis_id'] = str(uuid.uuid4())
                analysis_data[session['analysis_id']] = {
                    'results': results,
                    'filepath': filepath,
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify({
                    'success': True,
                    'analysis_id': session['analysis_id'],
                    'redirect': url_for('loading', analysis_id=session['analysis_id'])
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 400
    
    return render_template('upload.html')

@app.route('/loading/<analysis_id>')
def loading(analysis_id):
    session['analysis_id'] = analysis_id
    return render_template('loading.html', analysis_id=analysis_id)

@app.route('/dashboard/<analysis_id>')
def dashboard(analysis_id):
    if analysis_id not in analysis_data:
        return redirect(url_for('index'))
    
    data = analysis_data[analysis_id]
    return render_template('dashboard.html', analysis_id=analysis_id, **data['results'])

@app.route('/predict', methods=['POST'])
def predict():
    text = request.json.get('text', '')
    analysis_id = request.json.get('analysis_id', '')
    
    if analysis_id not in analysis_data:
        return jsonify({'error': 'No analysis found'}), 404
    
    analyzer = SentimentAnalyzer()
    analyzer.model = joblib.load(os.path.join(app.config['MODEL_FOLDER'], f'model_{analysis_id}.joblib'))
    analyzer.vectorizer = joblib.load(os.path.join(app.config['MODEL_FOLDER'], f'vectorizer_{analysis_id}.joblib'))
    
    prediction = analyzer.predict_single(text)
    return jsonify(prediction)

@app.route('/download_report/<analysis_id>')
def download_report(analysis_id):
    if analysis_id not in analysis_data:
        return "Report not found", 404
    
    data = analysis_data[analysis_id]
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        textColor=colors.darkblue,
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("AI Sentiment Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Stats table
    stats_data = [
        ['Metric', 'Value'],
        ['Total Reviews', str(data['results']['total_reviews'])],
        ['Positive %', f"{data['results']['positive_pct']:.1f}%"],
        ['Negative %', f"{data['results']['negative_pct']:.1f}%"],
        ['Neutral %', f"{data['results']['neutral_pct']:.1f}%"],
        ['Accuracy', f"{data['results']['accuracy']:.1f}%"]
    ]
    
    table = Table(stats_data)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    story.append(table)
    
    # Suggestions
    story.append(Spacer(1, 20))
    story.append(Paragraph("AI Suggestions:", styles['Heading2']))
    for suggestion in data['results']['suggestions']:
        story.append(Paragraph(f"• {suggestion}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        io.BytesIO(buffer.getvalue()),
        as_attachment=True,
        download_name=f"sentiment_report_{analysis_id}.pdf",
        mimetype='application/pdf'
    )

@app.route('/api/charts/<analysis_id>')
def get_charts(analysis_id):
    if analysis_id not in analysis_data:
        return jsonify({'error': 'Analysis not found'}), 404
    
    data = analysis_data[analysis_id]
    return jsonify(data['results'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)