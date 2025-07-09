import logging
import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import NamedTupleCursor

load_dotenv()
logger = logging.getLogger(__name__)


class UrlRepository:
    @staticmethod
    def get_connection():
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            logger.debug("Database connection verified")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    @staticmethod
    def execute_query(query, params=None, fetch=False, fetch_one=False):
        conn = None
        try:
            conn = UrlRepository.get_connection()
            with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
                cur.execute(query, params or ())
                
                if fetch_one:
                    result = cur.fetchone()
                    logger.debug(f"Query executed, fetched one row: {result}")
                    conn.commit()
                    return result
                
                if fetch:
                    result = cur.fetchall()
                    logger.debug(f"Query executed, fetched {len(result)} rows")
                    conn.commit()
                    return result
                
                conn.commit()
                logger.debug("Query executed successfully (no fetch)")
                return None
                
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    def find_url_by_name(name):
        logger.info(f"Searching URL by name: {name}")
        return UrlRepository.execute_query(
            "SELECT * FROM urls WHERE name = %s",
            (name,),
            fetch_one=True
        )

    @staticmethod
    def create_url(name):
        logger.info(f"Creating new URL: {name}")
        try:
            result = UrlRepository.execute_query(
                '''INSERT INTO urls (name, created_at) 
                VALUES (%s, %s) RETURNING id''',
                (name, datetime.now()),
                fetch_one=True
            )
            logger.info(f"URL created successfully, ID: {result.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create URL: {str(e)}")
            raise

    @staticmethod
    def find_url_by_id(id):
        return UrlRepository.execute_query(
            "SELECT * FROM urls WHERE id = %s",
            (id,),
            fetch_one=True
        )

    @staticmethod
    def create_url_check(url_id, status_code, h1, title, description):
        return UrlRepository.execute_query(
            """INSERT INTO url_checks (
                url_id, status_code, h1, title, description, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)""",
            (url_id, status_code, h1, title, description, datetime.now())
        )

    @staticmethod
    def get_url_checks(url_id):
        return UrlRepository.execute_query(
            """SELECT * FROM url_checks 
            WHERE url_id = %s ORDER BY created_at DESC""",
            (url_id,),
            fetch=True
        )

    @staticmethod
    def get_all_urls_with_last_check():
        return UrlRepository.execute_query(
            """SELECT 
                u.id, u.name,
                MAX(uc.created_at) as last_check_date,
                uc.status_code as last_status_code
            FROM urls u
            LEFT JOIN url_checks uc ON u.id = uc.url_id
            GROUP BY u.id, uc.status_code
            ORDER BY u.created_at DESC""",
            fetch=True
        )