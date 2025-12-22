from flask import Blueprint, request, make_response, url_for
from app.database import session_scope
from sqlalchemy import select
import json
from app.models import (
    ConstructionTableOptionData,
)

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