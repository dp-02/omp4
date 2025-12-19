from flask import Blueprint, request, make_response, url_for, render_template
from app.database import session_scope
from sqlalchemy import select
from flask import session as flask_session
import json
from app.models import (
    User,
    Checklist,
    ChecklistTableData
)

blueprint = Blueprint('api_checklist', __name__)

@blueprint.route('/create', methods=['POST'])
def create():
    ''' 建立檢查表 '''
    response = make_response()
    check_date = request.form.get('check_date')
    site_uid = request.form.get('site_uid')
    check_type = request.form.get('check_type')
    user_uid = flask_session['user_uid']

    with session_scope() as session:
        query1 = Checklist.create(session, check_date = check_date, site_uid = site_uid, check_type = check_type, user_uid = user_uid)

    trigger_data = {
            "response-data": {
                "title": "新增成功！",
                "text": f"檢查表已建立，即將轉跳...",
                "redirectUrl": url_for('view_checklist.choose_checklist', site_uid = site_uid, check_type = check_type)
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response

@blueprint.route('/get/site/<int:site_uid>/<int:check_type>', methods=['GET'])
def get_by_site(site_uid,check_type):
    data = {
        "site_uid":site_uid,
        "check_type":check_type
    }
    data_c = []
    with session_scope() as session:
        stmt = select(Checklist).where(Checklist.site_uid == site_uid, Checklist.check_type == check_type).order_by(Checklist.check_date)
        query = session.scalars(stmt).all()
        for item in query:
            user = User.get(session, uid = item.user_uid)
            data_c.append(Checklist.to_dict(item) | {"user_name":user.name})
            
    return render_template('checklist/partials/_checklist_list_items.html', data_c=data_c, data = data)

@blueprint.route('/save/<int:checklist_uid>', methods=['POST'])
def save_Checklist_data(checklist_uid):
    response = make_response()
    with session_scope() as session:
        form_data = request.form
        for option_uid_str, value in form_data.items():
            option_uid = int(option_uid_str)
            stmt = select(ChecklistTableData).where(
                ChecklistTableData.checklist_uid == checklist_uid,
                ChecklistTableData.option_uid == option_uid
            )
            record = session.execute(stmt).scalars().first()
            if record:
                if record.value != value:
                    record.value = value
            else:
                ChecklistTableData.create(
                    session,
                    checklist_uid=checklist_uid,
                    option_uid=option_uid,
                    value=value
                )
        trigger_data = {
                "response-data": {
                    "title": "資料已成功儲存！"
            }
        }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        
        return response
    
@blueprint.route('/delete/<int:checklist_uid>', methods=['DELETE'])
def api_delete_checklist(checklist_uid):
    with session_scope() as session:
        Checklist.delete(session, uid = checklist_uid)
    return '', 200