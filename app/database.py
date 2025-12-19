from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

Base = declarative_base()
Session = sessionmaker()

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def init(app:Flask):
    DATABASE_URL = app.config.get('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)