# app/__init__.py
from flask import Flask
from config import Config
# 從重構後的 database 引入 db 物件
from app.database import db  
from flask_migrate import Migrate

# 初始化 Migrate 物件
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY 未設定")
    
    # 1. 初始化資料庫 (Flask-SQLAlchemy)
    db.init_app(app)
    
    # 2. 初始化 Migration (綁定 app 和 db)
    # 這裡必須明確傳入 db，這樣 Alembic 才知道要追蹤哪個資料庫
    migrate.init_app(app, db)

    # 3. 引入 Model (非常重要！)
    # 必須在初始化 db 和 migrate 之後，但在回傳 app 之前引入
    # 這樣 Flask-Migrate 才能掃描到你的資料表定義
    from app.models import Auth, User

    # 初始化其他模組
    from app.views import init as init_views
    from app.api import init as init_api
    
    init_views(app)
    init_api(app)

    return app