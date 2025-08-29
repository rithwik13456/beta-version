from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
import json

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = relationship('Review', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.id}: {self.name}>'
        
    @property
    def total_reviews(self):
        return len(self.reviews)
    
    @property
    def avg_sentiment(self):
        if not self.reviews:
            return 0
        total_sentiment = sum([r.sentiment_score for r in self.reviews if r.sentiment_score is not None])
        return total_sentiment / len(self.reviews) if self.reviews else 0
    
    @property
    def sentiment_distribution(self):
        if not self.reviews:
            return {'positive': 0, 'negative': 0, 'neutral': 0}
        
        dist = {'positive': 0, 'negative': 0, 'neutral': 0}
        for review in self.reviews:
            if review.sentiment_label:
                dist[review.sentiment_label.lower()] += 1
        return dist

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(300))
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    rating = db.Column(db.Integer)  # 1-5 star rating if available
    
    # Sentiment Analysis Results
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))  # Positive, Negative, Neutral
    sentiment_confidence = db.Column(db.Float)
    positive_score = db.Column(db.Float)
    negative_score = db.Column(db.Float)
    neutral_score = db.Column(db.Float)
    
    # Text Analysis
    word_count = db.Column(db.Integer)
    readability_score = db.Column(db.Float)
    topics = db.Column(db.Text)  # JSON string of extracted topics
    keywords = db.Column(db.Text)  # JSON string of keywords
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)
    
    # Relationships
    replies = relationship('Reply', backref='review', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Review {self.id}: {self.title or "Untitled"}>' 
    
    @property
    def total_replies(self):
        return len(self.replies)
    
    @property
    def avg_reply_sentiment(self):
        if not self.replies:
            return None
        total_sentiment = sum([r.sentiment_score for r in self.replies if r.sentiment_score is not None])
        return total_sentiment / len(self.replies) if self.replies else None

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    
    # Sentiment Analysis Results
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))
    sentiment_confidence = db.Column(db.Float)
    positive_score = db.Column(db.Float)
    negative_score = db.Column(db.Float)
    neutral_score = db.Column(db.Float)
    
    # Text Analysis
    word_count = db.Column(db.Integer)
    keywords = db.Column(db.Text)  # JSON string of keywords
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Reply {self.id}: Review {self.review_id}>'

# Keep the old Analysis model for backward compatibility during transition
class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Analysis {self.id}: {self.url}>'