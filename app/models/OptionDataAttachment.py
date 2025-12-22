from app.database import Base
from sqlalchemy import Column, String, Integer, ForeignKey, and_
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session, relationship
from sqlalchemy.inspection import inspect
from datetime import datetime, date

class OptionDataAttachment(Base):
    ''' 選項資料附件 '''
    __tablename__ = 'option_data_attachment'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    table_type = Column(String(32), nullable=False, index=True)
    option_data_uid = Column(Integer, nullable=False, index=True)
    type = Column(String(32))

    construction_option_data = relationship(
        "ConstructionTableOptionData",
        primaryjoin="and_(foreign(OptionDataAttachment.option_data_uid) == ConstructionTableOptionData.uid, "
                    "OptionDataAttachment.table_type == 'construction')",
        back_populates="attachments",
        overlaps="checklist_option_data, attachments"
    )
    
    checklist_option_data = relationship(
        "ChecklistTableOptionData",
        primaryjoin="and_(foreign(OptionDataAttachment.option_data_uid) == ChecklistTableOptionData.uid, "
                    "OptionDataAttachment.table_type == 'checklist')",
        back_populates="attachments",
        overlaps="construction_option_data, attachments"
    )
    
    images = relationship("OptionDataAttachmentImage", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionDataAttachmentImage.uid")
    notes = relationship("OptionDataAttachmentNote", back_populates="attachment", cascade="all, delete-orphan", order_by="OptionDataAttachmentNote.uid")
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
        return f'<option_data_attachment {self.uid}>'