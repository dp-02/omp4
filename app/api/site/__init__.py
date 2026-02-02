from flask import Blueprint, request, make_response, url_for, render_template
from app.database import session_scope
from sqlalchemy import select, delete
from flask import session as flask_session
import json
from app.models import (
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule
)

blueprint = Blueprint('api_site', __name__)

@blueprint.route('/create', methods=['POST'])
def site_create():
    ''' 建立案場 '''
    def parse_site_form_data(form_data):
        ''' 將 form_data 轉換為巢狀結構'''
        phases_data = []
        try:
            phase_count = int(form_data.get('phase', 1))
        except ValueError:
            phase_count = 1
        for i in range(1, phase_count + 1):
            j,k = 1,1
            _tr = form_data.get(f'phase_taipower_rate{i}')
            phase_obj = {'name': form_data.get(f'phase_name{i}'), 'taipower_rate': int(_tr) if _tr and str(_tr).strip() else None, 'inverters': [],'modules': [], 'sort': i}
            while True:
                brand_key = f'inverter_brand{i}_{j}'
                if brand_key not in form_data: break
                inverter = {'brand': form_data.get(f'inverter_brand{i}_{j}'),'model': form_data.get(f'inverter_model{i}_{j}')}
                phase_obj['inverters'].append(inverter)
                j += 1
            while True:
                brand_key = f'module_brand{i}_{k}'
                if brand_key not in form_data: break
                module = {'brand': form_data.get(f'module_brand{i}_{k}'),'model': form_data.get(f'module_model{i}_{k}'),'wattage': form_data.get(f'module_wattage{i}_{k}')}
                phase_obj['modules'].append(module)
                k += 1
            phases_data.append(phase_obj)
        return phases_data
    
    response = make_response()
    name = request.form.get('name')
    region = request.form.get('region_index')
    address = request.form.get('address')
    company = request.form.get('company')
    build_date = request.form.get('build_date')
    wait_cheack = True if request.form.get('wait_cheack') else False
    user_uid = flask_session['user_uid']
    phase_number = int(request.form.get('phase', 1))
    _greenpower = request.form.get('greenpower_rate')
    greenpower_rate = int(_greenpower) if _greenpower and str(_greenpower).strip() else None

    structured_phases = parse_site_form_data(request.form)

    with session_scope() as session:
        query1 = Site.create(session, region = region, name = name, address = address, company = company, build_date = None if build_date == '' else build_date, wait_cheack = wait_cheack, phase_number = phase_number, user_uid = user_uid, greenpower_rate = greenpower_rate)
        for p_data in structured_phases:
            query2 = SitePhase.create(session, site_uid = query1.uid,  name = p_data['name'], sort = p_data['sort'], taipower_rate = p_data.get('taipower_rate'))
            for i_data in p_data['inverters']:
                SitePhaseInverter.create(session, phase_uid = query2.uid, brand = i_data['brand'], model = i_data['model'])
            for m_data in p_data['modules']:
                SitePhaseModule.create(session, phase_uid = query2.uid, brand = m_data['brand'], model = m_data['model'], wattage = m_data['wattage'])

    trigger_data = {
            "response-data": {
                "title": "新增成功！",
                "text": f"案場已建立，即將轉跳...",
                "redirectUrl": url_for('view_site.region', region_index = region)
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response


@blueprint.route('/update', methods=['POST'])
def site_update():
    ''' 更新案場 '''
    def parse_site_form_data(form_data):
        ''' 將 form_data 轉換為巢狀結構'''
        phases_data = []
        try:
            phase_count = int(form_data.get('phase', 1))
        except ValueError:
            phase_count = 1
        for i in range(1, phase_count + 1):
            j,k = 1,1
            _tr = form_data.get(f'phase_taipower_rate{i}')
            phase_obj = {'uid': form_data.get(f'phase_uid{i}'), 'name': form_data.get(f'phase_name{i}'), 'taipower_rate': int(_tr) if _tr and str(_tr).strip() else None, 'inverters': [],'modules': [], 'sort': i}
            while True:
                brand_key = f'inverter_brand{i}_{j}'
                if brand_key not in form_data: break
                inverter = {'uid': form_data.get(f'inverter_uid{i}_{j}'),'brand': form_data.get(f'inverter_brand{i}_{j}'),'model': form_data.get(f'inverter_model{i}_{j}')}
                phase_obj['inverters'].append(inverter)
                j += 1
            while True:
                brand_key = f'module_brand{i}_{k}'
                if brand_key not in form_data: break
                module = {'uid': form_data.get(f'module_uid{i}_{k}'),'brand': form_data.get(f'module_brand{i}_{k}'),'model': form_data.get(f'module_model{i}_{k}'),'wattage': form_data.get(f'module_wattage{i}_{k}')}
                phase_obj['modules'].append(module)
                k += 1
            phases_data.append(phase_obj)
        return phases_data
    
    response = make_response()
    site_uid = request.form.get('site_uid')
    name = request.form.get('name')
    region = request.form.get('region_index')
    address = request.form.get('address')
    company = request.form.get('company')
    build_date = request.form.get('build_date')
    wait_cheack = True if request.form.get('wait_cheack') else False
    _greenpower = request.form.get('greenpower_rate')
    greenpower_rate = int(_greenpower) if _greenpower and str(_greenpower).strip() else None

    structured_phases = parse_site_form_data(request.form)
    with session_scope() as session:
        Site.update(session, uid = site_uid, name = name, address = address, company = company, build_date = None if build_date == '' else build_date, wait_cheack = wait_cheack, greenpower_rate = greenpower_rate)
        stmt = delete(SitePhase).where(SitePhase.site_uid == site_uid)
        result = session.execute(stmt)
        for p_data in structured_phases:
            site_phase = SitePhase.create(session, site_uid = site_uid,  name = p_data['name'],  sort = p_data['sort'], taipower_rate = p_data.get('taipower_rate'))
            for i_data in p_data['inverters']:
                SitePhaseInverter.create(session, phase_uid = site_phase.uid, brand = i_data['brand'], model = i_data['model'])
            for m_data in p_data['modules']:
                SitePhaseModule.create(session, phase_uid = site_phase.uid, brand = m_data['brand'], model = m_data['model'], wattage = m_data['wattage'])

    trigger_data = {
            "response-data": {
                "title": "更新成功！",
                "text": f"案場已更新，即將轉跳...",
                "redirectUrl": url_for('view_site.region', region_index = region)
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    
    return response


@blueprint.route('/get/region/<int:region_index>', methods=['GET'])
def get_by_region(region_index):
    data_s = []
    with session_scope() as session:
        stmt = select(Site).where(Site.region == region_index).order_by(Site.name)
        query = session.scalars(stmt).all()
        for item in query:
            data_s.append(Site.to_dict(item))
    return render_template('site/partials/_site_list_items.html', data_s=data_s)

@blueprint.route('/delete/<int:site_uid>', methods=['DELETE'])
def api_delete_site(site_uid):
    with session_scope() as session:
        Site.delete(session, uid = site_uid)
    return '', 200