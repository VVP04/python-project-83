import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.extras import NamedTupleCursor
from requests.exceptions import RequestException

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


def validate_url(url):
    if not url:
        logger.warning("Empty URL submitted")
        flash('URL обязателен', 'danger')
        return False, render_template('index.html'), 422
        
    if not validators.url(url):
        logger.warning(f"Invalid URL format: {url}")
        flash('Некорректный URL', 'danger')
        return False, render_template('index.html'), 422
        
    if len(url) > 255:
        logger.warning(f"URL exceeds length limit: {url[:50]}...")
        flash('URL превышает 255 символов', 'danger')
        return False, render_template('index.html'), 422
    
    return True, None, None


def normalize_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def execute_db_query(query, params=None, fetch=False, fetch_one=False):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(query, params or ())
            if fetch_one:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            else:
                result = None
            conn.commit()
            return result
    except Exception as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url')
    logger.info(f"Received URL submission: {url}")

    is_valid, template, code = validate_url(url)
    if not is_valid:
        return template, code
    
    normalized_url = normalize_url(url)
    logger.info(f"Normalized URL: {normalized_url}")

    try:
        existing_url = execute_db_query(
            "SELECT id FROM urls WHERE name = %s",
            (normalized_url,),
            fetch_one=True
        )
        
        if existing_url:
            logger.info(f"URL already exists in DB, ID: {existing_url.id}")
            flash('Страница уже существует', 'info')
            return redirect(url_for('show_url', id=existing_url.id))
        
        new_url = execute_db_query(
            '''INSERT INTO urls (name, created_at) 
            VALUES (%s, %s) RETURNING id''',
            (normalized_url, datetime.now()),
            fetch_one=True
        )
        
        logger.info(f"Successfully added new URL, ID: {new_url.id}")
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=new_url.id))
            
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}", exc_info=True)
        flash(str(e), 'danger')
        return render_template('index.html'), 500


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        url = execute_db_query(
            "SELECT * FROM urls WHERE id = %s",
            (id,),
            fetch_one=True
        )
        
        if not url:
            logger.warning(f"URL not found for ID: {id}")
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        checks = execute_db_query(
            """SELECT 
                    id, 
                    status_code,
                    h1,
                    title,
                    description,
                    created_at 
                FROM url_checks 
                WHERE url_id = %s 
                ORDER BY created_at DESC""",
                (id,),
                fetch=True
            )
        
        logger.info(f"Successfully retrieved URL details for ID: {id}")
        return render_template('url.html', url=url, checks=checks or [])

    except Exception as e:
        logger.error(f"Error fetching URL details: {str(e)}", exc_info=True)
        flash('Ошибка при получении данных', 'danger')
        return redirect(url_for('index'))


@app.route('/urls')
def show_urls():
    try:
        urls = execute_db_query(
            """SELECT 
                u.id, 
                u.name, 
                u.created_at, 
                MAX(uc.created_at) as last_check_date,
                uc.status_code as last_status_code
            FROM urls u
            LEFT JOIN url_checks uc ON u.id = uc.url_id
            GROUP BY u.id, uc.status_code
            ORDER BY u.created_at DESC""",
            fetch=True
        )
        return render_template('urls.html', urls=urls)
    except Exception as e:
        logger.error(f"Error fetching URLs list: {str(e)}", exc_info=True)
        flash('Ошибка при получении списка страниц', 'danger')
        return render_template('urls.html', urls=[])


@app.post('/urls/<int:id>/checks')
def check_url(id):
    try:
        url = execute_db_query(
            "SELECT id, name FROM urls WHERE id = %s",
            (id,),
            fetch_one=True
        )
        
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('show_urls'))

        try:
            response = requests.get(
                url.name,
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            h1 = soup.find('h1')
            title = soup.find('title')
            description = soup.find('meta', attrs={'name': 'description'})
            
            execute_db_query(
                """INSERT INTO url_checks (
                    url_id, 
                    status_code,
                    h1,
                    title,
                    description, 
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    url.id,
                    response.status_code,
                    h1.get_text().strip() if h1 else None,
                    title.get_text().strip() if title else None,
                    description.get('content') if description else None,
                    datetime.now()
                )
            )
            
            flash('Страница успешно проверена', 'success')
            
        except RequestException as e:
            logger.error(f"Request failed for URL {url.name}: {str(e)}")
            flash('Произошла ошибка при проверке', 'danger')
            
    except Exception as e:
        logger.error(f"Error checking URL: {str(e)}", exc_info=True)
        flash('Внутренняя ошибка сервера', 'danger')
        
    return redirect(url_for('show_url', id=id))


if __name__ == '__main__':
    app.run()