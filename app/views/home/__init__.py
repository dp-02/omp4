from flask import Blueprint, render_template, request
from flask import session as flask_session
from app.database import session_scope
from app.auth import login_required
from app.models import (
    User,
)
blueprint = Blueprint('view_home', __name__)

@blueprint.route('/')
def index():
    ''' 首頁 '''
    return render_template('home/index.html')

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

    return render_template('home/choose_region.html')
