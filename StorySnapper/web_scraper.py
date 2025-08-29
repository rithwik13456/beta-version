import trafilatura
import requests
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> dict:
    """
    Extract text content from a website URL.
    Returns a dictionary with title, content, and metadata.
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        # Download the webpage
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise Exception("Failed to fetch content from URL")
        
        # Extract text content
        text = trafilatura.extract(downloaded)
        if not text:
            raise Exception("No content could be extracted from the webpage")
        
        # Extract title and other metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else "Untitled"
        
        return {
            'success': True,
            'title': title,
            'content': text,
            'url': url,
            'word_count': len(text.split()) if text else 0
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching {url}: {str(e)}")
        return {
            'success': False,
            'error': f"Network error: Unable to reach the website. Please check the URL and try again."
        }
    except ValueError as e:
        logger.error(f"Invalid URL {url}: {str(e)}")
        return {
            'success': False,
            'error': f"Invalid URL format. Please enter a valid URL starting with http:// or https://"
        }
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return {
            'success': False,
            'error': f"Failed to extract content: {str(e)}"
        }

def validate_url(url: str) -> bool:
    """
    Validate if the provided URL is properly formatted.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
