from flask import Blueprint, render_template, abort
from flask import session as flask_session
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    Checklist,
    ChecklistTable,
    ChecklistTableOptionData,
    ChecklistTableOption
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
    ''' 建立 '''
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
        stmt = select(ChecklistTableOptionData).where(ChecklistTableOptionData.checklist_uid == checklist_uid)
        results = session.execute(stmt).scalars().all()
        data['saved']  = {rec.option_uid: rec.value for rec in results}
    return render_template('Checklist/table.html', data = data)


@blueprint.route('/<int:site_uid>/<int:check_type>/<int:checklist_uid>/create_report/choose_option/')
@login_required
def create_rport_choose_option(site_uid, check_type, checklist_uid):
    ''' 表單 '''
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


    return render_template('Checklist/createReportChooseOption.html', data = data)