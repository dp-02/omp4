from flask import Flask
from config import Config
from app.views import init as init_views
from app.api import init as init_api
from .database import init as init_database 
from .models import (
    Auth,
    User
)

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config) 

    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY 未設定")
    
    init_database(app)
    init_views(app)
    init_api(app)

    return app