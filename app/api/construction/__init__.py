from flask import Blueprint, request, make_response, jsonify, render_template
from app.database import session_scope
from app.saveFile import save
from sqlalchemy import select
import json
from app.models import (
    ConstructionTableOptionData,
    ConstructionHazardNotice
)
from datetime import datetime

blueprint = Blueprint('api_construction', __name__)

@blueprint.route('/save/<int:site_uid>', methods=['POST'])
def save_construction_data(site_uid):
    response = make_response()
    with session_scope() as session:
        form_data = request.form
        for key, value in form_data.items():
            # 如果 key 不是純數字 (例如 "desc_123_456")，就跳過不處理
            if not key.isdigit():
                continue
            option_uid = int(key)
            stmt = select(ConstructionTableOptionData).where(
                ConstructionTableOptionData.site_uid == site_uid,
                ConstructionTableOptionData.option_uid == option_uid
            )
            record = session.execute(stmt).scalars().first()
            if record:
                if record.value != value:
                    record.value = value
            else:
                new_record = ConstructionTableOptionData(
                    site_uid=site_uid,
                    option_uid=option_uid,
                    value=value
                )
                session.add(new_record)
        trigger_data = {
                "start-attachment-upload": {
                    "site_uid": site_uid 
                }
            }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        
        return response
    
@blueprint.route('/hazard_notice/create', methods=['POST'])
def hazard_notice_create():
    saved_file_path = None
    file = request.files.get('file')
    if file: saved_file_path= save(file, "design")
    with session_scope() as session:
        ConstructionHazardNotice.create(
            session,
            site_uid = request.form.get('site_uid'),
            group_uid = request.form.get('group_uid'),
            note = request.form.get('note'),
            file_path = saved_file_path,
        )
        return jsonify({"message": "success"}), 200
    
@blueprint.route('/hazard_notice_options/get/<site_uid>/<group_uid>')
def api_get_hazard_options(site_uid, group_uid):
    data_option = []
    with session_scope() as session:
        stmt = select(ConstructionHazardNotice).where(ConstructionHazardNotice.site_uid ==site_uid, ConstructionHazardNotice.group_uid==group_uid).order_by(ConstructionHazardNotice.at_createdtime.desc())
        options = session.execute(stmt).scalars().all()
        for data_o in options:
            data_option.append(ConstructionHazardNotice.to_dict(data_o))
        for item in data_option:
            item['at_createdtime'] = datetime.fromisoformat(item['at_createdtime'])
    return render_template('construction/partials/_hazard_options.html', data_option=data_option)

@blueprint.route('/hazard_notice_detail/get')
def api_get_hazard_detail():
    data_detail = None
    uid = request.args.get('hazard_uid')
    if not uid:
        return ""

    with session_scope() as session:
        query = ConstructionHazardNotice.get(session, uid = uid)
        data_detail = ConstructionHazardNotice.to_dict(query)
    
    return render_template('construction/partials/_hazard_detail.html', data_detail=data_detail)