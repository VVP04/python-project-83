import os
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import NamedTupleCursor
import validators
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.post('/urls')
def add_url():
    url = request.form.get('url')
    
    if not url:
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 422
        
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422
        
    if len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return render_template('index.html'), 422
    
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
            existing_url = cur.fetchone()
            
            if existing_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', id=existing_url.id))
            
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            new_url = cur.fetchone()
            conn.commit()
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=new_url.id))
            
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('index.html'), 500

@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        
    if not url:
        flash('Страница не найдена', 'danger')
        return redirect(url_for('index'))
        
    return render_template('url.html', url=url)

@app.route('/urls')
def show_urls():
    conn = get_db_connection()
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
        
    return render_template('urls.html', urls=urls)