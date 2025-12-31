from flask import Blueprint, request, make_response, url_for, render_template
from app.database import session_scope
from sqlalchemy import select
from flask import session as flask_session
import json
from app.models import (
    User,
    Checklist,
    ChecklistTable,
    ChecklistTableOption,
    ChecklistTableOptionData,
    OptionAttachment,
    OptionAttachmentAnomalyState,
    OptionAttachmentForChecklist
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

@blueprint.route('/update', methods=['POST'])
def update():
    ''' 更新檢查表 '''
    response = make_response()
    uid = request.form.get('uid')
    check_date = request.form.get('check_date')
    site_uid = request.form.get('site_uid')
    check_type = request.form.get('check_type')

    with session_scope() as session:
        query1 = Checklist.update(session, uid = uid, check_date = check_date)

    trigger_data = {
            "response-data": {
                "title": "更新成功！",
                "text": f"檢查表已更新，即將轉跳...",
                "redirectUrl": url_for('view_checklist.choose_checklist', site_uid = site_uid, check_type = check_type)
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response

@blueprint.route('/save/<int:checklist_uid>', methods=['POST'])
def save_Checklist_data(checklist_uid):
    response = make_response()
    with session_scope() as session:
        form_data = request.form
        for key, value in form_data.items():
            if not key.isdigit(): continue
            option_uid = int(key)
            stmt = select(ChecklistTableOptionData).where(
                ChecklistTableOptionData.checklist_uid == checklist_uid,
                ChecklistTableOptionData.option_uid == option_uid
            )
            record = session.execute(stmt).scalars().first()
            if record:
                if record.value != value:
                    record.value = value
            else:
                ChecklistTableOptionData.create(
                    session,
                    checklist_uid=checklist_uid,
                    option_uid=option_uid,
                    value=value
                )
        trigger_data = {
            "start-attachment-upload": {
                "checklist_uid": checklist_uid 
            }
        }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        
        return response
    
@blueprint.route('/delete/<int:checklist_uid>', methods=['DELETE'])
def api_delete_checklist(checklist_uid):
    with session_scope() as session:
        Checklist.delete(session, uid = checklist_uid)
    return '', 200

@blueprint.route('/anomaly_state/get_partial/<site_uid>')
def get_anomaly_state_list_partial(site_uid):
    '''未處理事項'''
    data_options = []
    filter_state = request.args.get('filter_state', 'All') 

    with session_scope() as session:
        stmt = None
        if filter_state == 'All':
            stmt = select(OptionAttachment,
                          OptionAttachmentAnomalyState.value,
                          ChecklistTableOption.name,
                          ChecklistTableOption.sort,
                          ChecklistTable.uid,
                          ChecklistTable.name,
                          Checklist.uid,
                          Checklist.check_date,
                          Checklist.check_type,
                          ).join(
                ChecklistTableOptionData, OptionAttachment.option_uid == ChecklistTableOptionData.option_uid
            ).join(
                OptionAttachmentAnomalyState, OptionAttachmentAnomalyState.option_attachment_uid == OptionAttachment.uid
            ).join(
                ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid
            ).join(
                ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid
            ).join(
                Checklist, Checklist.uid == ChecklistTableOptionData.checklist_uid
            ).join(
                OptionAttachmentForChecklist, OptionAttachment.uid == OptionAttachmentForChecklist.option_attachment_uid
            ).where(
                Checklist.uid == OptionAttachmentForChecklist.checklist_uid,
                Checklist.site_uid == site_uid,
                OptionAttachment.type == "anomaly"
            )
        else:
            stmt = select(OptionAttachment,
                          OptionAttachmentAnomalyState.value,
                          ChecklistTableOption.name,
                          ChecklistTableOption.sort,
                          ChecklistTable.uid,
                          ChecklistTable.name,
                          Checklist.uid,
                          Checklist.check_date,
                          Checklist.check_type,
                          ).join(
                ChecklistTableOptionData, OptionAttachment.option_uid == ChecklistTableOptionData.option_uid
            ).join(
                OptionAttachmentAnomalyState, OptionAttachmentAnomalyState.option_attachment_uid == OptionAttachment.uid
            ).join(
                ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid
            ).join(
                ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid
            ).join(
                Checklist, Checklist.uid == ChecklistTableOptionData.checklist_uid
            ).where(
                OptionAttachmentAnomalyState.value == filter_state
            ).join(
                OptionAttachmentForChecklist, OptionAttachment.uid == OptionAttachmentForChecklist.option_attachment_uid
            ).where(
                Checklist.uid == OptionAttachmentForChecklist.checklist_uid,
                Checklist.site_uid == site_uid,
                OptionAttachment.type == "anomaly"
            )
        options = session.execute(stmt).all()
        for data_o in options:
            data_options.append({
                "site_uid":site_uid,
                "check_type":data_o[8],
                "checklist_uid":data_o[6],
                "table_uid":data_o[4],
                "table_name":data_o[5],
                "state":data_o[1],
                "check_date":data_o[7],
                "option_sort":data_o[3],
                "option_name":data_o[2]
            })

    return render_template('checklist/partials/_anomaly_state_list.html', data_options=data_options)