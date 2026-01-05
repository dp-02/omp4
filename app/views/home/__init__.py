from flask import Blueprint, render_template, request, flash, make_response
from flask import session as flask_session
from app.database import session_scope
from app.auth import login_required
from app.models import (
    User,
)
import json
import os
from dotenv import load_dotenv

blueprint = Blueprint('view_home', __name__)

load_dotenv()
PASSWORD = os.getenv('PASSWORD')

@blueprint.route('/')
def index():
    ''' 首頁 '''
    return render_template('home/index.html')

@blueprint.route('/choose_user/', methods=['POST'])
def choose_user():
    ''' 選擇使用者 '''
    pw = request.form.get('password')
    if pw == PASSWORD:
        flash('登入成功！', 'success') 
        return render_template('home/chooseUser.html')
    else:
        error_html = """
        <div class="flex items-center gap-2 text-error text-sm font-medium animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-4 w-4" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>密碼錯誤，請重試！</span>
        </div>
        """
        return error_html

@blueprint.route('/choose_region/', methods=['POST','GET'])
def choose_region():
    ''' 選擇地區 '''
    uid = request.form.get('user_uid')
    with session_scope() as session:
        query = User.get(session, uid=uid)
        if uid: 
            flask_session['user_uid'] = uid
            flask_session['user_name'] = query.name
            print(f'使用者登入 uid：{uid} name:{query.name}')

    return render_template('home/chooseRegion.html')
