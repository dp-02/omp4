from flask import Blueprint, render_template, request, abort
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import (
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule
)
blueprint = Blueprint('view_site', __name__)

region_map = {
        1: "北部",
        2: "中彰投",
        3: "雲嘉南",
        4: "高屏",
        5: "東部"
    }

@blueprint.route('/<int:site_uid>/')
@login_required
def index(site_uid):
    ''' 案場 '''
    with session_scope() as session:
        inverter = []
        module = []
        query1 = Site.get(session, uid = site_uid)
        stmt = select(SitePhase).where(SitePhase.site_uid == site_uid)
        query2 = session.scalars(stmt).all()
        for sp_data in query2:
            stmt = select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == sp_data.uid)
            query3 = session.scalars(stmt).all()
            for spi_data in query3:
                inverter.append(SitePhaseInverter.to_dict(spi_data))
            stmt = select(SitePhaseModule).where(SitePhaseModule.phase_uid == sp_data.uid)
            query4 = session.scalars(stmt).all()
            for spm_data in query4:
                module.append(SitePhaseModule.to_dict(spm_data))
        site = Site.to_dict(query1)
    data = {
        "site":site,
        "inverter":inverter,
        "module":module,
    }
    return render_template('site/index.html', data = data)

@blueprint.route('/region/<int:region_index>/')
@login_required
def region(region_index):
    ''' 地區案場 '''
    return render_template('site/region.html', region_name = region_map.get(region_index, "未知"), region_index = region_index)

@blueprint.route('/create/<int:region_index>/')
@login_required
def create(region_index):
    ''' 新增 '''
    return render_template('site/form.html', act = 'create', region_name = region_map.get(region_index, "未知"), region_index = region_index, data = {"phaseData":[]})

@blueprint.route('/update/<int:site_uid>/')
@login_required
def update(site_uid):
    ''' 更新 '''
    with session_scope() as session:
        site_obj = Site.get(session, uid = site_uid)
        if not site_obj:
            return abort(404)
        region_index = site_obj.region
        form_data = Site.to_dict(site_obj) 

        stmt = select(SitePhase).where(SitePhase.site_uid == site_obj.uid)
        phases = session.scalars(stmt).all()
        form_data['phase'] = len(phases)
        for i, phase in enumerate(phases, start=1):
            form_data[f'phase_uid{i}'] = phase.uid
            form_data[f'phase_name{i}'] = phase.name
            form_data[f'phase_taipower_rate{i}'] = phase.taipower_rate if phase.taipower_rate is not None else ''
            stmt_inv = select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == phase.uid)
            inverters = session.scalars(stmt_inv).all()
            for j, inv in enumerate(inverters, start=1):
                form_data[f'inverter_uid{i}_{j}'] = inv.uid
                form_data[f'inverter_brand{i}_{j}'] = inv.brand
                form_data[f'inverter_model{i}_{j}'] = inv.model
            stmt_mod = select(SitePhaseModule).where(SitePhaseModule.phase_uid == phase.uid)
            modules = session.scalars(stmt_mod).all()
            for k, mod in enumerate(modules, start=1):
                form_data[f'module_uid{i}_{k}'] = mod.uid
                form_data[f'module_brand{i}_{k}'] = mod.brand
                form_data[f'module_model{i}_{k}'] = mod.model
                form_data[f'module_wattage{i}_{k}'] = mod.wattage
    return render_template('site/form.html', 
                           act='update', 
                           region_name=region_map.get(region_index, "未知"), 
                           region_index=region_index, 
                           data=form_data)

@blueprint.route('/partials/phases/')
def get_site_phases():
    ''' 處理期數的新增/減少 '''
    try:
        phase_count = int(request.args.get('phase', 1))
    except ValueError:
        phase_count = 1
    form_data = request.args 
    return render_template('site/partials/_phases.html', phase_count=phase_count, data=form_data)

@blueprint.route('/partials/sub-items/<item_type>/<int:phase_idx>/', methods=['POST'])
def update_sub_items(item_type, phase_idx):
    ''' 處理逆變器或模組的新增/減少 '''
    form_data = request.form
    op = request.args.get('op', 'add')
    current_count = 0
    prefix = f"{item_type}_brand{phase_idx}_"
    
    for key in form_data.keys():
        if key.startswith(prefix):
            try:
                idx = int(key.replace(prefix, ""))
                if idx > current_count:
                    current_count = idx
            except ValueError:
                continue

    if op == 'add':
        current_count += 1
    elif op == 'reduce' and current_count > 0:
        current_count -= 1
        
    return render_template('site/partials/_site_sub_items.html', 
                           item_type=item_type,
                           phase_idx=phase_idx,
                           count=current_count,
                           data=form_data)