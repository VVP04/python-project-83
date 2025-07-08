import logging

import validators
from flask import flash, render_template

logger = logging.getLogger(__name__)


def validate_url(url):
    if not url:
        logger.warning("Empty URL submitted")
        flash('URL обязателен', 'danger')
        return False, render_template('index.html'), 422
        
    if not validators.url(url):
        logger.warning(f"Invalid URL: {url}")
        flash('Некорректный URL', 'danger')
        return False, render_template('index.html'), 422
        
    if len(url) > 255:
        logger.warning(f"URL too long: {url[:50]}...")
        flash('URL превышает 255 символов', 'danger')
        return False, render_template('index.html'), 422
    
    return True, None, None