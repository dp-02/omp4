from flask import Blueprint, request, make_response, url_for, render_template, jsonify
from app.database import session_scope
from app.saveFile import save
from sqlalchemy import select
from flask import session as flask_session
from app.models import (
    DesignTableOption,
    DesignChecklist,
    DesignTableOptionData
)
import json

blueprint = Blueprint('api_design', __name__)

@blueprint.route('/<graph_type>/create', methods=['POST'])
def create(graph_type):
    response = make_response()
    site_uid = request.form.get('siteUid')
    table_uid = request.form.get('tableUid')
    note = request.form.get('note')
    phase = request.form.get('phase')
    
    checked_items = request.form.getlist('option_uid') 

    file_cad = request.files.get('file_cad')
    file_pdf = request.files.get('file_pdf')
    
    saved_file_cad_path = None
    saved_file_pdf_path = None

    if file_cad: saved_file_cad_path= save(file_cad, "design")
    if file_pdf: saved_file_pdf_path= save(file_pdf, "design")

    with session_scope() as session:
        query1 = DesignChecklist.create(session, 
                                        table_uid = table_uid, 
                                        site_uid = site_uid,
                                        note = note,
                                        type = graph_type,
                                        phase = phase,
                                        file_path_cad = saved_file_cad_path,
                                        file_path_pdf = saved_file_pdf_path)
        for option_uid in checked_items:
            DesignTableOptionData.create(
                session,
                option_uid = option_uid,
                design_checklist_uid = query1.uid,
                value = "on"
            )
    
    trigger_data = {
            "response-data": {
                "title": "新增成功！",
                "text": f"已新增設計規範確認表！"
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response

@blueprint.route('/<graph_type>/get_table_details', methods=['GET'])
def get_table_details(graph_type):
    options = []
    histories = []
    site_uid = request.args.get('siteUid')
    table_uid = request.args.get('tableUid')

    with session_scope() as session:
        stmt = select(DesignTableOption).where(DesignTableOption.table_uid == table_uid)
        query = session.execute(stmt).scalars().all()
        for data_o in query:
            options.append(DesignTableOption.to_dict(data_o))
        stmt = select(DesignChecklist).where(
            DesignChecklist.table_uid == table_uid,
            DesignChecklist.site_uid == site_uid,
            DesignChecklist.type == graph_type,
        ).order_by(DesignChecklist.at_createdtime.desc())
        query = session.execute(stmt).scalars().all()
        for data_d in query:
            histories.append(DesignChecklist.to_dict(data_d))
    
    return render_template(
        'design/partials/_table_details_swap.html',
        options=options,
        histories=histories,
        graph_type = graph_type
    )

@blueprint.route('/<graph_type>/get_history_details', methods=['GET'])
def get_history_details(graph_type):
    designlist_data = None
    options = []
    designlist_options = []
    designlist_uid = request.args.get('designlistUid')
    table_uid  = request.args.get('tableUid')
    records_map = {}
    
    if not designlist_uid:
        return "", 204 # 如果沒有 ID，不做任何事

    with session_scope() as session:
        stmt = select(DesignChecklist).where(DesignChecklist.uid == designlist_uid, DesignChecklist.type == graph_type)
        query = session.execute(stmt).scalar()
        designlist_data = DesignTableOption.to_dict(query)

        stmt_data = select(DesignTableOptionData).where(DesignTableOptionData.design_checklist_uid == designlist_uid)
        query_data = session.execute(stmt_data).scalars().all()
        records_map = {
            data.option_uid: DesignTableOptionData.to_dict(data) for data in query_data
        }
        stmt_opts = select(DesignTableOption).where(DesignTableOption.table_uid == table_uid)
        query_opts = session.execute(stmt_opts).scalars().all()
        
        for data_o in query_opts:
            opt_dict = DesignTableOption.to_dict(data_o)
            record = records_map.get(opt_dict['uid']) 
            opt_dict['has_record'] = True if record else False
            options.append(opt_dict)

        stmt = select(DesignChecklist.uid).where(DesignChecklist.type == graph_type).order_by(DesignChecklist.at_createdtime.desc()).limit(1)
        latest_uid = session.execute(stmt).scalar()
        is_latest = str(latest_uid) == designlist_uid if latest_uid else False
        designlist_data['is_latest'] = is_latest

    return render_template(
        'design/partials/_history_details_swap.html',
        designlist_options=designlist_options,
        options = options,
        designlist_data=designlist_data
    )