from flask import Blueprint, render_template, request
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    ConstructionTable,
    ConstructionTableGroup,
    ConstructionTableOption,
    ConstructionTableOptionData,
    OptionAttachment,
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule
)
blueprint = Blueprint('view_construction', __name__)

@blueprint.route('/<int:site_uid>/')
@login_required
def choose_group(site_uid):
    ''' 選擇大表 '''
    data = {
        "site_uid":site_uid,
        "group":[]
    }
    with session_scope() as session:
        stmt = select(ConstructionTableGroup.uid, ConstructionTableGroup.name)
        query = session.execute(stmt).all()
        for data_g in query:
            data['group'].append({
                "uid":data_g[0],
                "name":data_g[1]
            })
    return render_template('construction/chooseGroup.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/')
@login_required
def choose_table(site_uid, group_uid):
    ''' 選擇表 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "table":[]
    }
    with session_scope() as session:
        stmt = select(ConstructionTable.uid, ConstructionTable.name).where(
            ConstructionTable.group_uid == group_uid
            ).order_by(ConstructionTable.sort)
        query = session.execute(stmt).mappings().all()
        for data_t in query:
            data['table'].append({
                "uid":data_t.uid,
                "name":data_t.name
            })
    return render_template('construction/chooseTable.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/<int:table_uid>/')
@login_required
def table(site_uid, group_uid, table_uid):
    ''' 表單 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "table_uid":table_uid,
        "table_name":"",
        "saved":[],
        "options":[]
    }
    with session_scope() as session:
        stmt = select(ConstructionTableOption).where(
            ConstructionTableOption.table_uid == table_uid
            ).order_by(ConstructionTableOption.sort)
        query = session.execute(stmt).scalars().all()
        for data_o in query:
            data['options'].append(ConstructionTableOption.to_dict(data_o))
        stmt = select(ConstructionTable.name).where(ConstructionTable.uid == table_uid)
        query = session.execute(stmt).scalar()
        data['table_name'] = query
        stmt = select(ConstructionTableOptionData).where(ConstructionTableOptionData.site_uid == site_uid)
        results = session.execute(stmt).scalars().all()
        data['saved']  = {rec.option_uid: rec.value for rec in results}
    return render_template('construction/table.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/hazard_notice/')
@login_required
def hazard_notice(site_uid, group_uid):
    ''' 每日危害通知單 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "group_name":""
    }
    with session_scope() as session:
        group = ConstructionTableGroup.get(session, uid = group_uid)
        data['group_name'] = group.name
    return render_template('construction/hazardNotice.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/create_report_choose_option/')
@login_required
def create_report_choose_option(site_uid, group_uid):
    ''' 生成報告選項 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "group_name":"",
        "table":[]
    }
    with session_scope() as session:
        group = ConstructionTableGroup.get(session, uid = group_uid)
        data['group_name'] = group.name

        stmt = select(ConstructionTable).where(ConstructionTable.group_uid == group_uid)
        tables = session.execute(stmt).scalars()
        for data_t in tables:
            data['table'].append({
                "uid":data_t.uid,
                "name":data_t.name,
                "options":[]
            })
    return render_template('construction/createReportChooseOption.html', data = data)


@blueprint.route('/<int:site_uid>/<int:group_uid>/report/', methods=['POST'])
@login_required
def create_rport(site_uid, group_uid):
    ''' 產生報告 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "group_name":"",
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

    final_report_data = [item['uid'] for item in selected_items.values() if item['uid']]

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

        stmt = select(
                ConstructionTableOptionData,
                ConstructionTableOption,
                ConstructionTable,
                OptionAttachment).join(
                ConstructionTableOption, ConstructionTableOption.uid == ConstructionTableOptionData.option_uid
            ).join(
                ConstructionTable, ConstructionTable.uid == ConstructionTableOption.table_uid
            ).where(
                ConstructionTableOptionData.site_uid == site_uid,
                OptionAttachment.site_uid == site_uid,
                ConstructionTable.group_uid == group_uid,
                ConstructionTable.uid.in_(final_report_data)
            )
        query = session.execute(stmt).all()
        for data_table in query:
            construction_table_option_data = data_table[0]
            construction_table_option = data_table[1]
            construction_table = data_table[2]
            option_attachment = data_table[3]
            if construction_table.uid not in data['table']: 
                data['table'][construction_table.uid]  = {
                    "name":construction_table.name,
                    "options":{}
                }
            if construction_table_option.uid not in data['table'][construction_table.uid]['options']: 
                data['table'][construction_table.uid]['options'][construction_table_option.uid] = {
                    "name":construction_table_option.name,
                    "sort":construction_table_option.sort,
                    "value":construction_table_option_data.value,
                    "attachment":[]
                }
            if option_attachment.option_uid == construction_table_option.uid: 
                    data['table'][construction_table.uid]['options'][construction_table_option.uid]['attachment'].append(option_attachment.uid)
    return render_template('construction/createReport.html', data = data)