import logging
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .page_checker import SiteChecker
from .repository import UrlRepository
from .url_normalizer import normalize_url
from .url_validation import validate_url

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url')
    is_valid, template, code = validate_url(url)
    if not is_valid:
        return template, code
    
    normalized_url = normalize_url(url)
    
    try:
        existing_url = UrlRepository.find_url_by_name(normalized_url)
        if existing_url:
            flash('Страница уже существует', 'info')
            return redirect(url_for('show_url', id=existing_url.id))
        
        new_url = UrlRepository.create_url(normalized_url)
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=new_url.id))
        
    except Exception as e:
        logger.error(f"Error adding URL: {str(e)}")
        flash(str(e), 'danger')
        return render_template('index.html'), 500


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        url = UrlRepository.find_url_by_id(id)
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        checks = UrlRepository.get_url_checks(url.id)
        return render_template('url.html', url=url, checks=checks)
        
    except Exception as e:
        logger.error(f"Error showing URL: {str(e)}")
        flash('Ошибка при получении данных', 'danger')
        return redirect(url_for('index'))


@app.route('/urls')
def show_urls():
    try:
        urls = UrlRepository.get_all_urls_with_last_check()
        return render_template('urls.html', urls=urls)
    except Exception as e:
        logger.error(f"Error listing URLs: {str(e)}")
        flash('Ошибка при получении списка', 'danger')
        return render_template('urls.html', urls=[])


@app.post('/urls/<int:id>/checks')
def check_url(id):
    try:
        url = UrlRepository.find_url_by_id(id)
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('show_urls'))

        check_data = SiteChecker.perform_check(url.name)
        UrlRepository.create_url_check(
            url.id,
            check_data['status_code'],
            check_data['h1'],
            check_data['title'],
            check_data['description']
        )
        flash('Страница успешно проверена', 'success')
        
    except Exception as e:
        logger.error(f"Error checking URL: {str(e)}")
        flash('Произошла ошибка при проверке', 'danger')
        
    return redirect(url_for('show_url', id=id))


if __name__ == '__main__':
    app.run()