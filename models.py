# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Taxpayer(Base):
    """Налогоплательщики"""
    __tablename__ = "taxpayers"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=False)
    snils = Column(String(14), index=True)
    full_name = Column(String(255), nullable=False)
    passport_series = Column(String(4))
    passport_number = Column(String(6))
    passport_issued_by = Column(Text)
    passport_issue_date = Column(DateTime)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    messages = relationship("Message", back_populates="taxpayer")

class Message(Base):
    """Сообщения из ЕФРСБ"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_number = Column(String(50), unique=True, index=True)
    external_id = Column(String(100), index=True)
    message_date = Column(DateTime)
    debtor_name = Column(String(255))
    debtor_inn = Column(String(12), index=True)
    debtor_snils = Column(String(14))
    message_type = Column(String(100))
    status = Column(String(50))
    details_url = Column(Text)
    raw_data = Column(Text)  # JSON с полными данными
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Внешний ключ
    taxpayer_id = Column(Integer, ForeignKey("taxpayers.id"))
    
    # Связи
    taxpayer = relationship("Taxpayer", back_populates="messages")
