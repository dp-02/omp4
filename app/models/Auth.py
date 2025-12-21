from app.database import Base
from sqlalchemy import Column, Boolean, DateTime, Integer
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from datetime import datetime, date

class Auth(Base):
    ''' 權限 '''
    __tablename__ = 'auth'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    user_uid = Column(Integer)
    state = Column(Integer)
    admin = Column(Boolean)
    at_createdtime = Column(DateTime, default=datetime.now)
    at_editedtime = Column(DateTime)
    at_deletedtime = Column(DateTime)

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
        return f'<auth {self.user_uid}>'