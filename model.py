import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib
import re
import os
from collections import Counter
from datetime import datetime

class SentimentAnalyzer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.accuracy = 0
        
    def clean_text(self, text):
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def detect_text_column(self, df):
        text_columns = ['review', 'text', 'comment', 'feedback', 'description']
        for col in text_columns:
            if col in df.columns and df[col].dtype == 'object':
                return col
        # Fallback to first string column
        for col in df.columns:
            if df[col].dtype == 'object':
                return col
        raise ValueError("No suitable text column found")
    
    def generate_suggestions(self, results):
        suggestions = []
        pos_pct = results['positive_pct']
        neg_pct = results['negative_pct']
        
        if neg_pct > 40:
            suggestions.append("High negative sentiment detected - urgent attention required")
        if pos_pct > 70:
            suggestions.append("Excellent customer satisfaction - leverage in marketing")
        if results['negative_keywords']:
            suggestions.append(f"Address common complaints: {', '.join(results['negative_keywords'][:3])}")
        if results['positive_keywords']:
            suggestions.append(f"Strengths: {', '.join(results['positive_keywords'][:3])}")
            
        suggestions.extend([
            "Consider sentiment tracking over time",
            "Segment analysis by customer demographics",
            "A/B test response strategies for negative feedback"
        ])
        
        return suggestions[:5]
    
    def extract_keywords(self, texts, labels, top_n=10):
        word_counts = Counter()
        for text, label in zip(texts, labels):
            words = self.clean_text(text).split()
            word_counts.update(words)
        
        return [word for word, _ in word_counts.most_common(top_n)]
    
    def analyze_dataset(self, filepath, model_folder='static/models'):
        df = pd.read_csv(filepath)
        
        # Detect text column
        text_col = self.detect_text_column(df)
        df[text_col] = df[text_col].apply(self.clean_text)
        df = df.dropna(subset=[text_col])
        
        # Simple rule-based labeling for demo (in production, use labeled data)
        def simple_label(text):
            text = text.lower()
            pos_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'awesome']
            neg_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'disappointed']
            
            pos_score = sum(1 for word in pos_words if word in text)
            neg_score = sum(1 for word in neg_words if word in text)
            
            if pos_score > neg_score:
                return 'positive'
            elif neg_score > pos_score:
                return 'negative'
            else:
                return 'neutral'
        
        df['sentiment'] = df[text_col].apply(simple_label)
        
        # Prepare data
        texts = df[text_col].values
        labels = df['sentiment'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Vectorize
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)
        
        # Train model
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_train_tfidf, y_train)
        
        # Predict and evaluate
        y_pred = self.model.predict(X_test_tfidf)
        self.accuracy = accuracy_score(y_test, y_pred) * 100
        
        # Full dataset predictions
        X_full_tfidf = self.vectorizer.transform(texts)
        full_pred = self.model.predict(X_full_tfidf)
        full_pred_proba = self.model.predict_proba(X_full_tfidf)
        
        # Statistics
        sentiment_counts = pd.Series(full_pred).value_counts()
        total_reviews = len(full_pred)
        
        results = {
            'total_reviews': total_reviews,
            'sentiment_counts': dict(sentiment_counts),
            'positive_pct': (sentiment_counts.get('positive', 0) / total_reviews) * 100,
            'negative_pct': (sentiment_counts.get('negative', 0) / total_reviews) * 100,
            'neutral_pct': (sentiment_counts.get('neutral', 0) / total_reviews) * 100,
            'accuracy': self.accuracy,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'predictions': full_pred.tolist(),
            'probabilities': full_pred_proba.tolist(),
            'texts': texts.tolist(),
            'positive_keywords': self.extract_keywords(texts[full_pred == 'positive'], full_pred),
            'negative_keywords': self.extract_keywords(texts[full_pred == 'negative'], full_pred),
            'suggestions': self.generate_suggestions(results)
        }
        
        # Save model
        analysis_id = os.path.basename(filepath).split('.')[0]
        joblib.dump(self.model, os.path.join(model_folder, f'model_{analysis_id}.joblib'))
        joblib.dump(self.vectorizer, os.path.join(model_folder, f'vectorizer_{analysis_id}.joblib'))
        
        return results
    
    def predict_single(self, text):
        if not self.model or not self.vectorizer:
            return {'error': 'Model not trained'}
        
        clean_text = self.clean_text(text)
        text_tfidf = self.vectorizer.transform([clean_text])
        pred = self.model.predict(text_tfidf)[0]
        proba = self.model.predict_proba(text_tfidf)[0]
        confidence = max(proba) * 100
        
        return {
            'sentiment': pred.title(),
            'confidence': f"{confidence:.1f}%",
            'probabilities': {k.title(): f"{v*100:.1f}%" for k, v in zip(self.model.classes_, proba[0])}
        }