import logging

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class SiteChecker:
    @staticmethod
    def perform_check(url):
        try:
            response = requests.get(
                url,
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return {
                'status_code': response.status_code,
                'h1': SiteChecker._extract_tag_content(soup, 'h1'),
                'title': SiteChecker._extract_tag_content(soup, 'title'),
                'description': SiteChecker._extract_meta_description(soup)
            }
            
        except RequestException as e:
            logger.error(f"Check failed for {url}: {str(e)}")
            raise

    @staticmethod
    def _extract_tag_content(soup, tag_name):
        tag = soup.find(tag_name)
        return tag.get_text().strip() if tag else None

    @staticmethod
    def _extract_meta_description(soup):
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content') if meta else None