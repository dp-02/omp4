from app.database import Base
from sqlalchemy import Column, String, Integer, ForeignKey, and_
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session, relationship
from sqlalchemy.inspection import inspect
from datetime import datetime, date

class OptionAttachment(Base):
    ''' 選項資料附件 '''
    __tablename__ = 'option_attachment'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    option_uid = Column(Integer, nullable=False, index=True)
    table_type = Column(String(32), nullable=False, index=True)
    type = Column(String(32))

    construction_option = relationship(
        "ConstructionTableOption",
        primaryjoin="and_(foreign(OptionAttachment.option_uid) == ConstructionTableOption.uid, "
                    "OptionAttachment.table_type == 'construction')",
        back_populates="attachments",
        overlaps="checklist_option, attachments"
    )
    
    checklist_option = relationship(
        "ChecklistTableOption",
        primaryjoin="and_(foreign(OptionAttachment.option_uid) == ChecklistTableOption.uid, "
                    "OptionAttachment.table_type == 'checklist')",
        back_populates="attachments",
        overlaps="construction_option, attachments"
    )
    
    images = relationship("OptionAttachmentImage", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentImage.uid")
    notes = relationship("OptionAttachmentNote", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentNote.uid")
    anomaly_breakers = relationship("OptionAttachmentAnomalyBreaker", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyBreaker.uid")
    anomaly_damageds = relationship("OptionAttachmentAnomalyDamaged", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyDamaged.uid")
    anomaly_images = relationship("OptionAttachmentAnomalyImage", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyImage.uid")
    anomaly_optimizers = relationship("OptionAttachmentAnomalyOptimizer", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyOptimizer.uid")
    anomaly_positions = relationship("OptionAttachmentAnomalyPosition", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyPosition.uid")
    anomaly_reasons = relationship("OptionAttachmentAnomalyReason", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyReason.uid")
    anomaly_states = relationship("OptionAttachmentAnomalyState", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionAttachmentAnomalyState.uid")
    # region CRUD

    @classmethod
    def create(cls, session: Session, **kwargs):
        '''新增一筆資料'''
        row = cls(**kwargs)
        session.add(row)
        session.flush() 
        session.refresh(row) 
        return row
        
    @classmethod
    def get(cls, session: Session, uid):
        '''取得一筆資料'''
        stmt = select(cls).where(cls.uid == uid)
        return session.scalars(stmt).first()

    @classmethod
    def update(cls, session: Session, uid, **kwargs):
        '''更新一筆資料'''
        stmt = update(cls).where(cls.uid == uid).values(**kwargs).execution_options(synchronize_session="fetch")
        result = session.execute(stmt)
        return result.rowcount
    
    @classmethod
    def delete(cls, session: Session, uid):
        '''刪除一筆資料'''
        stmt = delete(cls).where(cls.uid == uid)
        result = session.execute(stmt)
        return result.rowcount
    
    # endregion

    def to_dict(self):
        '''自動將所有欄位轉換成字典'''
        result = {}
        for c in inspect(self).mapper.column_attrs:
            value = getattr(self, c.key)
            if isinstance(value, (datetime, date)):
                result[c.key] = value.isoformat()
            else:
                result[c.key] = value
        return result
    
    def __repr__(self):
        return f'<option_attachment {self.uid}>'