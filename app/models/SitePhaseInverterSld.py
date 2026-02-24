from app.database import db
from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session, relationship
from sqlalchemy.inspection import inspect
from datetime import datetime, date


class SitePhaseInverterSld(db.Model):
    ''' 案場期數逆變器 SLD（單線圖）'''
    __tablename__ = 'site_phase_inverter_sld'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    inverter_uid = Column(Integer, ForeignKey('site_phase_inverter.uid', ondelete='CASCADE'), nullable=False)

    inv = Column(String(256))           # 逆變器
    mppt = Column(String(256))          # MPPT
    string = Column(String(256))        # 串
    orientation = Column(String(64))   # 方位
    tilt_angle = Column(Float)          # 角度
    module_wattage = Column(Float)      # 模組瓦數
    module_count = Column(Integer)      # 模組片數

    inverter = relationship("SitePhaseInverter", back_populates="slds")

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
        return f'<site_phase_inverter_sld {self.uid}>'
