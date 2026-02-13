from flask import Blueprint, render_template, abort, request
from flask import session as flask_session
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    Checklist,
    ChecklistTable,
    ChecklistTableOptionData,
    ChecklistTableOption,
    OptionAttachment,
    OptionAttachmentForChecklist,
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule,
    User
)
blueprint = Blueprint('view_checklist', __name__)

@blueprint.route('/<int:site_uid>/<int:check_type>/')
@login_required
def choose_checklist(site_uid, check_type):
    ''' 首頁 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type
    }
    return render_template('checklist/chooseChecklist.html', data = data)

@blueprint.route('/<int:site_uid>/<int:check_type>/create/')
@login_required
def create(site_uid, check_type):
    ''' 建立 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type,
        "user_name":flask_session['user_name']
    }
    return render_template('checklist/form.html', act="create", data = data)

@blueprint.route('/<int:checklist_uid>/update/')
@login_required
def update(checklist_uid):
    ''' 更新 '''
    with session_scope() as session:
        checklist_obj = Checklist.get(session, uid = checklist_uid)
        if not checklist_obj:
            return abort(404)
        data = {
            "uid":checklist_obj.uid,
            "site_uid":checklist_obj.site_uid,
            "check_type":checklist_obj.check_type,
            "check_date":checklist_obj.check_date,
            "user_name":flask_session['user_name']
        }
    return render_template('checklist/form.html', act="update", data = data)

@blueprint.route('/<int:site_uid>/<int:check_type>/<int:checklist_uid>/')
@login_required
def choose_table(site_uid, check_type, checklist_uid):
    ''' 選擇表 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type,
        "checklist_uid":checklist_uid,
        "table":[],
        "checked":[]
    }
    with session_scope() as session:
        stmt = select(ChecklistTable.uid, ChecklistTable.name).order_by(ChecklistTable.sort)
        query = session.execute(stmt).mappings().all()
        for data_t in query:
            data['table'].append({
                "uid":data_t.uid,
                "name":data_t.name
            })
        stmt = select(ChecklistTableOption.table_uid).distinct().join(
            ChecklistTableOptionData, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid
            ).where(ChecklistTableOptionData.checklist_uid == checklist_uid)
        query = session.execute(stmt).mappings().all()
        for data_t in query:
            data['checked'].append(data_t.table_uid)
    return render_template('checklist/chooseTable.html', data = data)

@blueprint.route('/<int:site_uid>/<int:check_type>/<int:checklist_uid>/<int:table_uid>/')
@login_required
def table(site_uid, check_type, checklist_uid, table_uid):
    ''' 表單 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type,
        "checklist_uid":checklist_uid,
        "table_name":"",
        "table_note":"",
        "table_uid":0,
        "saved":[],
        "options":[]
    }
    with session_scope() as session:
        stmt = select(ChecklistTableOption).where(
            ChecklistTableOption.table_uid == table_uid
            ).order_by(ChecklistTableOption.sort)
        query = session.execute(stmt).scalars().all()
        for data_o in query:
            data['options'].append(ChecklistTableOption.to_dict(data_o))
        stmt = select(ChecklistTable).where(ChecklistTable.uid == table_uid)
        query = session.execute(stmt).scalar()
        data['table_uid'] = query.uid
        data['table_name'] = query.name
        data['table_note'] = query.note if query.note else ''
        stmt = select(ChecklistTableOptionData).where(ChecklistTableOptionData.checklist_uid == checklist_uid)
        results = session.execute(stmt).scalars().all()
        data['saved']  = {rec.option_uid: rec.value for rec in results}
    return render_template('checklist/table.html', data = data)


@blueprint.route('/<int:site_uid>/<int:check_type>/<int:checklist_uid>/create_report/choose_option/')
@login_required
def create_rport_choose_option(site_uid, check_type, checklist_uid):
    ''' 產生報告選擇選項 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type,
        "checklist_uid":checklist_uid,
        "table":[]
    }
    with session_scope() as session:
        stmt = select(ChecklistTable)
        tables = session.execute(stmt).scalars()
        for data_t in tables:
            data['table'].append({
                "uid":data_t.uid,
                "name":data_t.name,
                "options":[]
            })
            if check_type == 2 :
                stmt = select(ChecklistTableOption).where(ChecklistTableOption.table_uid == data_t.uid).order_by(ChecklistTableOption.sort)
                options = session.execute(stmt).scalars()
                for data_o in options:
                    data['table'][-1]['options'].append({
                        "uid":data_o.uid,
                        "name":data_o.name
                    }
                    )


    return render_template('checklist/createReportChooseOption.html', data = data)

@blueprint.route('/<int:site_uid>/<int:check_type>/<int:checklist_uid>/report/', methods=['POST'])
@login_required
def create_rport(site_uid, check_type, checklist_uid):
    ''' 產生報告 '''
    data = {
        "site_uid":site_uid,
        "check_type":check_type,
        "checklist_uid":checklist_uid,
        "table":{}
    }
    selected_items = {}

    for key, value in request.form.items():
        if not key.startswith('option'):
            continue
        clean_key = key.replace('option', '')
        if '_' in clean_key:
            parts = clean_key.split('_')
            parent_idx = parts[0]
            child_idx = parts[1]
            if parent_idx not in selected_items: selected_items[parent_idx] = {'uid': None, 'children': []}
            selected_items[parent_idx]['children'].append({
                "uid":value,
                "index":child_idx
            })
        else:
            parent_idx = clean_key
            if parent_idx not in selected_items: selected_items[parent_idx] = {'uid': value, 'children': []}

    final_report_data = []
    
    if check_type == 1: # 檢測
        final_report_data = [item['uid'] for item in selected_items.values() if item['uid']]
    elif check_type == 2: # 維修
        for idx, item in selected_items.items():
            final_report_data.append({
                'parent_uid': item['uid'],
                'selected_options': item['children']
            })

    with session_scope() as session:
        # 案場、逆變器、模組資料（報告頂部顯示用）
        inverter = []
        module = []
        query_site = Site.get(session, uid=site_uid)
        if query_site:
            data['site'] = Site.to_dict(query_site)
            stmt_phase = select(SitePhase).where(SitePhase.site_uid == site_uid)
            for sp_data in session.scalars(stmt_phase).all():
                for spi_data in session.scalars(select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == sp_data.uid)).all():
                    inverter.append(SitePhaseInverter.to_dict(spi_data))
                for spm_data in session.scalars(select(SitePhaseModule).where(SitePhaseModule.phase_uid == sp_data.uid)).all():
                    module.append(SitePhaseModule.to_dict(spm_data))
        else:
            data['site'] = None
        data['inverter'] = inverter
        data['module'] = module

        checklist_obj = Checklist.get(session, uid=checklist_uid)
        data['checklist'] = Checklist.to_dict(checklist_obj) if checklist_obj else None
        if checklist_obj and checklist_obj.user_uid:
            user = User.get(session, uid=checklist_obj.user_uid)
            data['inspector_name'] = user.name if user else None
        else:
            data['inspector_name'] = None

        if check_type == 1: # 檢測
            stmt = select(ChecklistTableOptionData,ChecklistTableOption,ChecklistTable,OptionAttachment
            ).join(
                ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid
            ).join(
                ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid
            ).join(
                OptionAttachmentForChecklist, OptionAttachmentForChecklist.checklist_uid == ChecklistTableOptionData.checklist_uid
            ).join(
                OptionAttachment, OptionAttachment.uid == OptionAttachmentForChecklist.option_attachment_uid
            ).where(
                ChecklistTableOptionData.checklist_uid == checklist_uid,
                ChecklistTable.uid.in_(final_report_data)
            ).order_by(
                ChecklistTable.sort
            )
            query = session.execute(stmt).all()
            for data_table in query:
                checklist_table_option_data = data_table[0]
                checklist_table_option = data_table[1]
                checklist_table = data_table[2]
                option_attachment = data_table[3]
                if checklist_table.uid not in data['table']: 
                    data['table'][checklist_table.uid]  = {
                        "name":checklist_table.name,
                        "options":{}
                    }
                if checklist_table_option.uid not in data['table'][checklist_table.uid]['options']: 
                    data['table'][checklist_table.uid]['options'][checklist_table_option.uid] = {
                        "name":checklist_table_option.name,
                        "sort":checklist_table_option.sort,
                        "value":checklist_table_option_data.value,
                        "attachment":[]
                    }
                if option_attachment.option_uid == checklist_table_option.uid: 
                    data['table'][checklist_table.uid]['options'][checklist_table_option.uid]['attachment'].append(option_attachment.uid)
        elif check_type == 2: # 維修
            all_options = [opt['uid'] for item in final_report_data for opt in item['selected_options']]
            stmt = select(ChecklistTableOptionData,ChecklistTableOption,ChecklistTable,OptionAttachment
            ).join(
                ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid
            ).join(
                ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid
            ).join(
                OptionAttachmentForChecklist, OptionAttachmentForChecklist.checklist_uid == ChecklistTableOptionData.checklist_uid
            ).join(
                OptionAttachment, OptionAttachment.uid == OptionAttachmentForChecklist.option_attachment_uid
            ).where(
                ChecklistTableOptionData.checklist_uid == checklist_uid,
                ChecklistTableOption.uid.in_(all_options)
            ).order_by(
                ChecklistTableOption.sort
            )
            query = session.execute(stmt).all()
            for data_table in query:
                checklist_table_option_data = data_table[0]
                checklist_table_option = data_table[1]
                checklist_table = data_table[2]
                option_attachment = data_table[3]
                if checklist_table.uid not in data['table']: 
                    data['table'][checklist_table.uid]  = {
                        "name":checklist_table.name,
                        "options":{}
                    }
                if checklist_table_option.uid not in data['table'][checklist_table.uid]['options']: 
                    data['table'][checklist_table.uid]['options'][checklist_table_option.uid] = {
                        "name":checklist_table_option.name,
                        "sort":checklist_table_option.sort,
                        "value":checklist_table_option_data.value,
                        "attachment":[]
                    }
                if option_attachment.option_uid == checklist_table_option.uid: 
                    data['table'][checklist_table.uid]['options'][checklist_table_option.uid]['attachment'].append(option_attachment.uid)
    return render_template('checklist/createReport.html', data = data)

@blueprint.route('/<int:site_uid>/anomaly_state/')
@login_required
def anomaly_state(site_uid):
    ''' 未處裡事項 '''
    data = {
        "site_uid":site_uid
    }
    return render_template('checklist/anomalyState.html', data = data)
