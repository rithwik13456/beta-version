from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Analysis, Project, Review, Reply
from web_scraper import get_website_text_content, validate_url
from analysis import analyzer
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Dashboard with overview and analytics."""
    # Get overall statistics
    total_projects = Project.query.count()
    total_reviews = Review.query.count()
    total_replies = Reply.query.count()
    
    # Recent activity
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.updated_at.desc()).limit(3).all()
    
    # Sentiment distribution across all reviews
    all_reviews = Review.query.all()
    sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
    if all_reviews:
        for review in all_reviews:
            if review.sentiment_label:
                sentiment_dist[review.sentiment_label.lower()] += 1
    
    # Calculate average sentiment
    avg_sentiment = 0
    if all_reviews:
        total_sentiment = sum([r.sentiment_score for r in all_reviews if r.sentiment_score is not None])
        avg_sentiment = total_sentiment / len(all_reviews) if all_reviews else 0
    
    stats = {
        'total_projects': total_projects,
        'total_reviews': total_reviews,
        'total_replies': total_replies,
        'avg_sentiment': round(avg_sentiment, 3),
        'sentiment_distribution': sentiment_dist
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_reviews=recent_reviews,
                         recent_projects=recent_projects)

@app.route('/projects')
def projects():
    """List all projects."""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return render_template('projects.html', projects=projects)

@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    """Create a new project."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Project name is required.', 'error')
            return render_template('new_project.html')
        
        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.commit()
        
        flash(f'Project "{name}" created successfully!', 'success')
        return redirect(url_for('project_details', project_id=project.id))
    
    return render_template('new_project.html')

@app.route('/projects/<int:project_id>')
def project_details(project_id):
    """View project details and analytics."""
    project = Project.query.get_or_404(project_id)
    
    # Get reviews with pagination
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(project_id=project_id)\
                         .order_by(Review.created_at.desc())\
                         .paginate(page=page, per_page=10, error_out=False)
    
    # Analytics data
    sentiment_over_time = []
    if project.reviews:
        # Group by week for trend analysis
        for i in range(4):  # Last 4 weeks
            week_start = datetime.utcnow() - timedelta(weeks=i+1)
            week_end = datetime.utcnow() - timedelta(weeks=i)
            week_reviews = [r for r in project.reviews 
                          if week_start <= r.created_at <= week_end and r.sentiment_score is not None]
            
            if week_reviews:
                avg_sentiment = sum([r.sentiment_score for r in week_reviews]) / len(week_reviews)
                sentiment_over_time.append({
                    'week': f'Week {4-i}',
                    'sentiment': round(avg_sentiment, 3),
                    'count': len(week_reviews)
                })
    
    return render_template('project_details.html', 
                         project=project, 
                         reviews=reviews,
                         sentiment_over_time=sentiment_over_time)

@app.route('/projects/<int:project_id>/add-review', methods=['GET', 'POST'])
def add_review(project_id):
    """Add a review to a project."""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        author = request.form.get('author', '').strip()
        source_url = request.form.get('source_url', '').strip()
        rating = request.form.get('rating', type=int)
        
        if not content:
            flash('Review content is required.', 'error')
            return render_template('add_review.html', project=project)
        
        # Create review
        review = Review(
            project_id=project_id,
            title=title,
            content=content,
            author=author,
            source_url=source_url,
            rating=rating,
            word_count=len(content.split())
        )
        
        # Analyze sentiment
        try:
            analysis_result = analyzer.analyze_content(content, title)
            if analysis_result['success']:
                review.sentiment_score = analysis_result['sentiment']['compound']
                review.sentiment_label = analysis_result['sentiment']['label']
                review.sentiment_confidence = analysis_result.get('sentiment_confidence', 0)
                review.positive_score = analysis_result['sentiment']['positive']
                review.negative_score = analysis_result['sentiment']['negative']
                review.neutral_score = analysis_result['sentiment']['neutral']
                review.readability_score = analysis_result['statistics'].get('readability_score', 0)
                review.keywords = json.dumps(analysis_result.get('keywords', []))
                review.analyzed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error analyzing review: {str(e)}")
            flash("Review saved but sentiment analysis failed.", 'warning')
        
        db.session.add(review)
        
        # Update project timestamp
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Review added successfully!', 'success')
        return redirect(url_for('project_details', project_id=project_id))
    
    return render_template('add_review.html', project=project)

@app.route('/reviews/<int:review_id>')
def review_details(review_id):
    """View review details with replies."""
    review = Review.query.get_or_404(review_id)
    return render_template('review_details.html', review=review)

@app.route('/reviews/<int:review_id>/add-reply', methods=['POST'])
def add_reply(review_id):
    """Add a reply to a review."""
    review = Review.query.get_or_404(review_id)
    
    content = request.form.get('content', '').strip()
    author = request.form.get('author', '').strip()
    
    if not content:
        flash('Reply content is required.', 'error')
        return redirect(url_for('review_details', review_id=review_id))
    
    # Create reply
    reply = Reply(
        review_id=review_id,
        content=content,
        author=author,
        word_count=len(content.split())
    )
    
    # Analyze sentiment
    try:
        analysis_result = analyzer.analyze_content(content)
        if analysis_result['success']:
            reply.sentiment_score = analysis_result['sentiment']['compound']
            reply.sentiment_label = analysis_result['sentiment']['label']
            reply.sentiment_confidence = analysis_result.get('sentiment_confidence', 0)
            reply.positive_score = analysis_result['sentiment']['positive']
            reply.negative_score = analysis_result['sentiment']['negative']
            reply.neutral_score = analysis_result['sentiment']['neutral']
            reply.keywords = json.dumps(analysis_result.get('keywords', []))
            reply.analyzed_at = datetime.utcnow()
    except Exception as e:
        logger.error(f"Error analyzing reply: {str(e)}")
        flash("Reply saved but sentiment analysis failed.", 'warning')
    
    db.session.add(reply)
    db.session.commit()
    
    flash('Reply added successfully!', 'success')
    return redirect(url_for('review_details', review_id=review_id))

@app.route('/analytics')
def analytics():
    """Advanced analytics and insights page."""
    # Get all data for comprehensive analysis
    projects = Project.query.all()
    reviews = Review.query.all()
    replies = Reply.query.all()
    
    # Overall metrics
    metrics = {
        'total_projects': len(projects),
        'total_reviews': len(reviews),
        'total_replies': len(replies),
        'avg_sentiment': 0,
        'sentiment_trend': [],
        'top_keywords': [],
        'project_performance': []
    }
    
    # Calculate average sentiment
    if reviews:
        total_sentiment = sum([r.sentiment_score for r in reviews if r.sentiment_score is not None])
        metrics['avg_sentiment'] = round(total_sentiment / len(reviews), 3)
    
    # Sentiment trend over last 30 days
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=i)
        day_reviews = [r for r in reviews 
                      if r.created_at.date() == date.date() and r.sentiment_score is not None]
        
        if day_reviews:
            avg_sentiment = sum([r.sentiment_score for r in day_reviews]) / len(day_reviews)
            metrics['sentiment_trend'].append({
                'date': date.strftime('%Y-%m-%d'),
                'sentiment': round(avg_sentiment, 3),
                'count': len(day_reviews)
            })
    
    # Top keywords across all reviews
    all_keywords = []
    for review in reviews:
        if review.keywords:
            try:
                keywords = json.loads(review.keywords)
                all_keywords.extend(keywords)
            except:
                pass
    
    if all_keywords:
        from collections import Counter
        keyword_count = Counter(all_keywords)
        metrics['top_keywords'] = keyword_count.most_common(20)
    
    # Project performance comparison
    for project in projects:
        if project.reviews:
            metrics['project_performance'].append({
                'name': project.name,
                'review_count': len(project.reviews),
                'avg_sentiment': round(project.avg_sentiment, 3),
                'sentiment_distribution': project.sentiment_distribution
            })
    
    return render_template('analytics.html', metrics=metrics)

# API endpoints for dashboard charts
@app.route('/api/sentiment-data/<int:project_id>')
def api_sentiment_data(project_id):
    """API endpoint for sentiment chart data."""
    project = Project.query.get_or_404(project_id)
    
    # Get sentiment data for the last 30 days
    data = []
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=i)
        day_reviews = [r for r in project.reviews 
                      if r.created_at.date() == date.date()]
        
        sentiment_scores = [r.sentiment_score for r in day_reviews if r.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'sentiment': round(avg_sentiment, 3),
            'count': len(day_reviews)
        })
    
    return jsonify(data)

# Keep old routes for backward compatibility
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Legacy analyze route - redirect to new project system."""
    if request.method == 'POST':
        flash('Please create a project first to organize your reviews.', 'info')
        return redirect(url_for('new_project'))
    return redirect(url_for('new_project'))

@app.route('/history')
def history():
    """Legacy history route - redirect to projects."""
    return redirect(url_for('projects'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template('500.html'), 500