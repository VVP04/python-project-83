import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.extras import NamedTupleCursor


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        logger.info("Successfully connected to database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url')
    logger.info(f"Received URL submission: {url}")

    if not url:
        logger.warning("Empty URL submitted")
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 422
        
    if not validators.url(url):
        logger.warning(f"Invalid URL format: {url}")
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422
        
    if len(url) > 255:
        logger.warning(f"URL exceeds length limit: {url[:50]}...")
        flash('URL превышает 255 символов', 'danger')
        return render_template('index.html'), 422
    
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    logger.info(f"Normalized URL: {normalized_url}")

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:

            cur.execute(
                "SELECT id FROM urls WHERE name = %s", (normalized_url,)
                )
            existing_url = cur.fetchone()
            
            if existing_url:
                logger.info(f"URL already exists in DB, ID: {existing_url.id}")
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', id=existing_url.id))
            
            cur.execute(
                '''INSERT INTO urls (name, created_at) 
                VALUES (%s, %s) RETURNING id''',
                (normalized_url, datetime.now())
            )
            new_url = cur.fetchone()
            conn.commit()
            logger.info(f"Successfully added new URL, ID: {new_url.id}")
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=new_url.id))
            
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}", exc_info=True)
        flash(str(e), 'danger')
        return render_template('index.html'), 500


@app.route('/urls/<int:id>')
def show_url(id):
    logger.info(f"Requested URL details for ID: {id}")
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
        
        if not url:
            logger.warning(f"URL not found for ID: {id}")
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
            
        logger.info(f"Successfully retrieved URL details for ID: {id}")
        return render_template('url.html', url=url)

    except Exception as e:
        logger.error(f"Error fetching URL details: {str(e)}", exc_info=True)
        flash('Ошибка при получении данных', 'danger')
        return redirect(url_for('index'))


@app.route('/urls')
def show_urls():
    logger.info("Requesting all URLs list")
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
            urls = cur.fetchall()
            logger.info(f"Retrieved {len(urls)} URLs from database")
        return render_template('urls.html', urls=urls)

    except Exception as e:
        logger.error(f"Error fetching URLs list: {str(e)}", exc_info=True)
        flash('Ошибка при получении списка страниц', 'danger')
        return render_template('urls.html', urls=[])


if __name__ == '__main__':
    app.run()