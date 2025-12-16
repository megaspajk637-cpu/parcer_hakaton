# celery_app.py
from celery import Celery
from app.parsers.efrsb_parser import EfrsbParser
from app.services.notification import NotificationService
import logging

celery_app = Celery(
    'tax_parser',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

parser = EfrsbParser()
notifier = NotificationService()

@celery_app.task
def parse_messages_task(filters=None, pages=10):
    """Фоновая задача парсинга нескольких страниц"""
    all_messages = []
    
    for page in range(1, pages + 1):
        try:
            html = parser.get_messages_page(page=page, filters=filters)
            messages = parser.parse_messages_table(html)
            all_messages.extend(messages)
            
            # Сохраняем каждые 100 сообщений
            if len(all_messages) % 100 == 0:
                save_messages_task.delay(all_messages[-100:])
                
        except Exception as e:
            logging.error(f"Ошибка на странице {page}: {e}")
            continue
    
    # Сохраняем оставшиеся сообщения
    if all_messages:
        save_messages_task.delay(all_messages)
    
    return {"total_parsed": len(all_messages)}

@celery_app.task
def save_messages_task(messages):
    """Сохранение сообщений в БД"""
    from app.crud import message_crud, taxpayer_crud
    
    saved = 0
    for msg in messages:
        try:
            # Ищем налогоплательщика
            taxpayer = None
            if msg.get('debtor_inn'):
                taxpayer = taxpayer_crud.get_by_inn(msg['debtor_inn'])
            
            # Создаем сообщение
            message_data = {
                **msg,
                'taxpayer_id': taxpayer.id if taxpayer else None
            }
            message_crud.create(message_data)
            saved += 1
            
        except Exception as e:
            logging.error(f"Ошибка сохранения сообщения: {e}")
    
    return {"saved": saved}
