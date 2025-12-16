# api/endpoints.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List
from datetime import date
import logging

from app.parsers.efrsb_parser import EfrsbParser
from app.services.notification import NotificationService
from app.crud import taxpayer_crud, message_crud
from app.schemas import (
    TaxpayerCreate, TaxpayerUpdate, MessageCreate,
    ParseRequest, ParseResult
)

router = APIRouter(prefix="/api/v1", tags=["parser"])
parser = EfrsbParser()
notifier = NotificationService()

@router.post("/parse/messages", response_model=ParseResult)
async def parse_efrsb_messages(
    request: ParseRequest,
    background_tasks: BackgroundTasks
):
    """
    Запуск парсинга сообщений из ЕФРСБ
    """
    try:
        # Парсим данные
        html = parser.get_messages_page(
            page=request.page,
            filters=request.filters
        )
        messages = parser.parse_messages_table(html)
        
        # Сохраняем в БД
        saved_count = 0
        for msg in messages:
            # Проверяем существование налогоплательщика по ИНН
            if msg.get('debtor_inn'):
                taxpayer = taxpayer_crud.get_by_inn(msg['debtor_inn'])
                if taxpayer:
                    message_data = MessageCreate(
                        **msg,
                        taxpayer_id=taxpayer.id
                    )
                    message_crud.create(message_data)
                    saved_count += 1
        
        # Запускаем фоновую задачу для отправки уведомлений
        background_tasks.add_task(
            notifier.send_batch_notifications,
            messages
        )
        
        return ParseResult(
            total_found=len(messages),
            saved_to_db=saved_count,
            messages=messages[:10]  # Возвращаем первые 10 для preview
        )
        
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse/excel")
async def parse_excel_report():
    """
    Парсинг Excel-файла с сообщениями
    """
    try:
        df = parser.download_excel_report()
        
        # Конвертируем DataFrame в JSON
        result = df.to_dict(orient='records')
        
        # Здесь можно добавить сохранение в БД
        return {
            "status": "success",
            "records_parsed": len(result),
            "data": result[:100]  # Ограничиваем вывод
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/search")
async def search_messages(
    inn: Optional[str] = Query(None),
    snils: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """
    Поиск сообщений по реквизитам
    """
    # Поиск в БД по параметрам
    filters = {}
    if inn:
        filters['debtor_inn'] = inn
    if snils:
        filters['debtor_snils'] = snils
    if name:
        filters['debtor_name__ilike'] = f"%{name}%"
    
    messages = message_crud.get_by_filters(filters)
    return messages
