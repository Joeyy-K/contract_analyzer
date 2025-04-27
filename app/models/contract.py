# app/models/contract.py (updated)
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base  

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf' or 'docx'
    content = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    analysis_results = Column(JSON, nullable=True) 
    user = relationship("User", back_populates="contracts")