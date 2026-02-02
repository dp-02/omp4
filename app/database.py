# app/database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# 定義 SQLAlchemy 2.0 的 Base 類別
class Base(DeclarativeBase):
    pass

# 初始化擴充套件，這裡還不需要綁定 app
db = SQLAlchemy(model_class=Base)

# 如果你原本習慣用 session_scope，可以用這個方式保留相容性，
# 但建議未來直接使用 db.session
from contextlib import contextmanager

@contextmanager
def session_scope():
    """提供一個交易範圍的 session"""
    session = db.session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    # 注意：在 Flask-SQLAlchemy 中，session 會由框架自動管理移除，通常不需要手動 close