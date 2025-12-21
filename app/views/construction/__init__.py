from flask import Blueprint, render_template
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    ConstructionTable,
    ConstructionTableGroup,
    ConstructionTableOption,
    ConstructionTableOptionData,
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