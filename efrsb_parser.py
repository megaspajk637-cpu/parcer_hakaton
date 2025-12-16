# parsers/efrsb_parser.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import asyncio
import aiohttp
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EfrsbParser:
    def __init__(self):
        self.base_url = "https://old.bankrot.fedresurs.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def get_messages_page(self, page: int = 1, filters: Optional[Dict] = None) -> str:
        """Получение страницы с сообщениями"""
        url = f"{self.base_url}/Messages.aspx"
        params = {
            'PageID': page,
            'page': page
        }
        
        if filters:
            params.update(filters)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении страницы: {e}")
            raise
    
    def parse_messages_table(self, html: str) -> List[Dict]:
        """Парсинг таблицы сообщений"""
        soup = BeautifulSoup(html, 'html.parser')
        messages = []
        
        # Находим таблицу с сообщениями (нужно уточнить селектор)
        table = soup.find('table', {'id': 'ctl00_cphBody_gvMessages'})
        
        if not table:
            # Пробуем другой возможный селектор
            table = soup.find('table', class_='grid')
        
        if table:
            rows = table.find_all('tr')[1:]  # Пропускаем заголовок
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    message = {
                        'message_number': cols[0].text.strip(),
                        'date': cols[1].text.strip(),
                        'debtor_name': cols[2].text.strip(),
                        'debtor_inn': self._extract_inn(cols[2].text),
                        'message_type': cols[3].text.strip(),
                        'status': cols[4].text.strip(),
                        'details_url': self._extract_link(cols[5])
                    }
                    messages.append(message)
        
        return messages
    
    def _extract_inn(self, text: str) -> Optional[str]:
        """Извлечение ИНН из текста"""
        import re
        inn_pattern = r'\b\d{10,12}\b'
        match = re.search(inn_pattern, text)
        return match.group(0) if match else None
    
    def _extract_link(self, cell) -> Optional[str]:
        """Извлечение ссылки на детали"""
        link = cell.find('a')
        if link and link.get('href'):
            return self.base_url + link['href']
        return None
    
    def download_excel_report(self, filters: Dict = None) -> pd.DataFrame:
        """Скачивание Excel отчета (если доступно)"""
        # Эмулируем клик по кнопке "Выгрузить в Excel"
        # Нужно исследовать форму на сайте
        
        # Временная заглушка - возвращаем DataFrame
        messages = self.parse_messages_table(self.get_messages_page())
        return pd.DataFrame(messages)
    
    async def parse_message_details(self, url: str) -> Dict:
        """Асинхронный парсинг деталей сообщения"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                return self._parse_details_page(html)
    
    def _parse_details_page(self, html: str) -> Dict:
        """Парсинг страницы с деталями сообщения"""
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Пример извлечения данных (нужно адаптировать под реальную структуру)
        details_table = soup.find('table', class_='details')
        if details_table:
            for row in details_table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().rstrip(':')
                    value = cols[1].text.strip()
                    details[key] = value
        
        return details
