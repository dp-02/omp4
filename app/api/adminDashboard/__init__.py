from flask import Blueprint, request, make_response, url_for
from app.database import session_scope
from sqlalchemy import select
import json
from app.models import (
    Auth,
    User
)

blueprint = Blueprint('api_adminDashboard', __name__)

@blueprint.route('/user/create', methods=['POST'])
def user_create():
    ''' 建立使用者 '''
    response = make_response()

    line_id = request.form.get('lineId')
    name = request.form.get('name')
    is_admin = request.form.get('admin') == 'on'

    with session_scope() as session:
        query1 = User.create(session, line_id = line_id, name = name)
        query2 = Auth.create(session, user_uid = query1.uid, state = 1, admin = is_admin)

    trigger_data = {
            "response-data": {
                "title": "新增成功！",
                "text": f"使用者 {name} 已建立，即將轉跳...",
                "redirectUrl": url_for('view_home.index')
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response


@blueprint.route('/user/get_all', methods=['GET'])
def user_get_all():
    ''' 取得全部使用者 '''
    response = make_response()
    datas = []

    with session_scope() as session:
        stmt = select(User).where()
        query = session.scalars(stmt).all()
        for item in query:
            datas.append(User.to_dict(item))
    trigger_data = {
        "response-data": datas
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response