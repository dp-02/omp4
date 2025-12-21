from flask import Blueprint, render_template
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    Site,
    SitePhase,
    DesignTable,
    DesignChecklist,
    DesignTableGroup,
    DesignTableOption,
    DesignTableOptionData,
)
blueprint = Blueprint('view_design', __name__)

@blueprint.route('/<int:site_uid>/')
@login_required
def choose_group(site_uid):
    ''' 選擇大表 '''
    data = {
        "site_uid":site_uid,
        "group":[]
    }
    with session_scope() as session:
        stmt = select(DesignTableGroup.uid, DesignTableGroup.name)
        query = session.execute(stmt).all()
        for data_g in query:
            data['group'].append({
                "uid":data_g[0],
                "name":data_g[1]
            })
    return render_template('design/chooseGroup.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/')
@login_required
def choose_phase(site_uid, group_uid):
    ''' 選擇期數 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "phase":[]
    }
    with session_scope() as session:
        stmt = select(SitePhase).where(SitePhase.site_uid == site_uid)
        query = session.scalars(stmt).all()
        for data_p in query:
            data['phase'].append(SitePhase.to_dict(data_p))
    return render_template('design/choosePhase.html', data = data)

@blueprint.route('/<int:site_uid>/<int:group_uid>/<int:phase_number>/')
@login_required
def table(site_uid, group_uid, phase_number):
    ''' 選擇表 '''
    data = {
        "site_uid":site_uid,
        "group_uid":group_uid,
        "phase":phase_number,
        "group_table":[],
        "options":[]
    }
    with session_scope() as session:
        stmt = select(DesignTable).where(DesignTable.group_uid == group_uid)
        query = session.scalars(stmt).all()
        for data_t in query:
            data['group_table'].append(DesignTable.to_dict(data_t))
    return render_template('design/table.html', data = data)
