from flask import Blueprint, request, make_response, url_for, render_template, jsonify
from app.database import session_scope
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
        user = User.create(session, line_id = line_id, name = name)
        auth = Auth.create(session, user_uid = user.uid, state = 1, admin = is_admin)

    trigger_data = {
            "response-data": {
                "title": "新增成功！",
                "text": f"使用者 {name} 已建立，即將轉跳...",
                "redirectUrl": url_for('view_admin_dashboard.index')
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

@blueprint.route('/partials/get_user_rows', methods=['GET'])
def get_user_rows():
    ''' 取得全部使用者 '''
    users = []
    with session_scope() as session:
        stmt = select(User).where()
        query = session.execute(stmt).scalars().all()
        for item in query:
            users.append(User.to_dict(item))
    return render_template('adminDashboard/partials/_user_rows.html', users=users)

@blueprint.route('/user/delete/<int:user_uid>', methods=['DELETE'])
def user_delete(user_uid):
    try:
        response = make_response("") 
        with session_scope() as session:
            deleted_count = User.delete(session, uid=user_uid)
            if not deleted_count: 
                return jsonify({"error": "使用者不存在"}), 404
        trigger_data = {
            "showToast": {
                "type": "success", 
                "message": f"使用者 (UID: {user_uid}) 已成功刪除"
            }
        }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        return response, 200
    except SQLAlchemyError as e:
        # 資料庫層面的錯誤 (如外鍵約束失敗)
        print(f"Database Error: {str(e)}")
        response = make_response(jsonify({"error": "無法刪除，該使用者可能尚有關聯資料。"}))
        trigger_data = {
            "showToast": {
                "type": "error", 
                "message": "刪除失敗：資料庫錯誤或資料有關聯"
            }
        }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        return response, 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": "伺服器內部錯誤"}), 500