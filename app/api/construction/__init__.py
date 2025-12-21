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
        for option_uid_str, value in form_data.items():
            option_uid = int(option_uid_str)
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
                "response-data": {
                    "title": "資料已成功儲存！"
            }
        }
        response.headers['HX-Trigger'] = json.dumps(trigger_data)
        
        return response