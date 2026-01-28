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
        msg = "密碼錯誤，請重新輸入！"
        resp = make_response(json.dumps({"message": msg}), 422)
        resp.headers['Content-Type'] = 'application/json'
        return resp

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
