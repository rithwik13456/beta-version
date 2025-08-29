import nltk
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import logging
from collections import Counter
from textstat import flesch_reading_ease, flesch_kincaid_grade
import re
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        
    def analyze_content(self, content: str, title: str = None) -> dict:
        """
        Perform comprehensive analysis of text content.
        """
        try:
            if not content or content.strip() == "":
                raise ValueError("No content provided for analysis")
            
            # Basic statistics
            word_count = len(content.split())
            char_count = len(content)
            sentences = sent_tokenize(content)
            sentence_count = len(sentences)
            
            # Average sentence length
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Readability scores
            try:
                readability_score = flesch_reading_ease(content)
                grade_level = flesch_kincaid_grade(content)
            except:
                readability_score = 0
                grade_level = 0
            
            # Sentiment analysis
            sentiment_scores = self.sia.polarity_scores(content)
            sentiment_label = self._get_sentiment_label(sentiment_scores['compound'])
            
            # Word frequency analysis
            words = word_tokenize(content.lower())
            words_filtered = [word for word in words if word.isalpha() and word not in self.stop_words]
            word_freq = Counter(words_filtered)
            top_words = word_freq.most_common(10)
            
            # Generate summary
            summary = self._generate_summary(content, sentences)
            
            # Create visualizations
            charts = self._create_visualizations(sentiment_scores, word_freq, top_words)
            
            # Extract keywords for storage
            keywords = [word for word, count in top_words]
            
            return {
                'success': True,
                'title': title or 'Untitled',
                'statistics': {
                    'word_count': word_count,
                    'character_count': char_count,
                    'sentence_count': sentence_count,
                    'avg_sentence_length': round(avg_sentence_length, 2),
                    'readability_score': round(readability_score, 2),
                    'grade_level': round(grade_level, 2)
                },
                'sentiment': {
                    'compound': round(sentiment_scores['compound'], 3),
                    'positive': round(sentiment_scores['pos'], 3),
                    'negative': round(sentiment_scores['neg'], 3),
                    'neutral': round(sentiment_scores['neu'], 3),
                    'label': sentiment_label
                },
                'top_words': top_words,
                'summary': summary,
                'charts': charts,
                'keywords': keywords,
                'sentiment_confidence': max(sentiment_scores['pos'], sentiment_scores['neg'], sentiment_scores['neu'])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}"
            }
    
    def _get_sentiment_label(self, compound_score: float) -> str:
        """
        Convert compound sentiment score to label.
        """
        if compound_score >= 0.05:
            return 'Positive'
        elif compound_score <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _generate_summary(self, content: str, sentences: list) -> str:
        """
        Generate a simple extractive summary.
        """
        try:
            if len(sentences) <= 3:
                return content
            
            # Simple summary: take first, middle, and last sentences
            summary_sentences = []
            summary_sentences.append(sentences[0])
            if len(sentences) > 2:
                summary_sentences.append(sentences[len(sentences) // 2])
            if len(sentences) > 1:
                summary_sentences.append(sentences[-1])
            
            return ' '.join(summary_sentences)
        except:
            return content[:500] + "..." if len(content) > 500 else content
    
    def _create_visualizations(self, sentiment_scores: dict, word_freq: Counter, top_words: list) -> dict:
        """
        Create base64 encoded charts for visualization.
        """
        charts = {}
        
        # Set style for dark theme
        plt.style.use('dark_background')
        
        try:
            # Sentiment chart
            sentiment_data = {
                'Positive': sentiment_scores['pos'],
                'Negative': sentiment_scores['neg'],
                'Neutral': sentiment_scores['neu']
            }
            
            fig, ax = plt.subplots(figsize=(8, 6))
            colors = ['#ff6b47', '#8b6914', '#52525b']  # Coral, muted brown, grey
            bars = ax.bar(sentiment_data.keys(), sentiment_data.values(), color=colors)
            ax.set_title('Sentiment Analysis', color='#e8e3d3', fontsize=16, pad=20)
            ax.set_ylabel('Score', color='#e8e3d3')
            ax.tick_params(colors='#e8e3d3')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.2f}', ha='center', va='bottom', color='#e8e3d3')
            
            plt.tight_layout()
            sentiment_chart = self._fig_to_base64(fig)
            charts['sentiment'] = sentiment_chart
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Error creating sentiment chart: {str(e)}")
        
        try:
            # Top words chart
            if top_words and len(top_words) > 0:
                words, counts = zip(*top_words[:8])  # Top 8 words
                
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(words, counts, color='#ff6b47')
                ax.set_title('Most Frequent Words', color='#e8e3d3', fontsize=16, pad=20)
                ax.set_xlabel('Frequency', color='#e8e3d3')
                ax.tick_params(colors='#e8e3d3')
                
                # Add value labels
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                           f'{int(width)}', ha='left', va='center', color='#e8e3d3')
                
                plt.tight_layout()
                words_chart = self._fig_to_base64(fig)
                charts['words'] = words_chart
                plt.close(fig)
                
        except Exception as e:
            logger.error(f"Error creating words chart: {str(e)}")
        
        return charts
    
    def _fig_to_base64(self, fig) -> str:
        """
        Convert matplotlib figure to base64 string.
        """
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', facecolor='#332621', 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        return f"data:image/png;base64,{img_str}"

# Global analyzer instance
analyzer = ContentAnalyzer()
