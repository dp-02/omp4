from flask import Blueprint, request, make_response, url_for, render_template
from app.database import session_scope
from sqlalchemy import select, delete
from flask import session as flask_session
import json
from app.models import (
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule,
    SitePhaseInverterSld,
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
            _gr = form_data.get(f'phase_greenpower_rate{i}')
            phase_obj = {'name': form_data.get(f'phase_name{i}'), 'taipower_rate': float(_tr) if _tr and str(_tr).strip() else None, 'greenpower_rate': float(_gr) if _gr and str(_gr).strip() else None, 'inverters': [], 'modules': [], 'sort': i}
            while True:
                brand_key = f'inverter_brand{i}_{j}'
                if brand_key not in form_data: break
                inverter = {'brand': form_data.get(f'inverter_brand{i}_{j}'), 'model': form_data.get(f'inverter_model{i}_{j}'), 'slds': []}
                k = 1
                while f'sld_inv{i}_{j}_{k}' in form_data:
                    inv_val = form_data.get(f'sld_inv{i}_{j}_{k}')
                    mppt_val = form_data.get(f'sld_mppt{i}_{j}_{k}')
                    string_val = form_data.get(f'sld_string{i}_{j}_{k}')
                    orientation_val = form_data.get(f'sld_orientation{i}_{j}_{k}')
                    tilt_val = form_data.get(f'sld_tilt_angle{i}_{j}_{k}')
                    tilt_angle = float(tilt_val) if tilt_val and str(tilt_val).strip() else None
                    watt_val = form_data.get(f'sld_module_wattage{i}_{j}_{k}')
                    module_wattage = float(watt_val) if watt_val and str(watt_val).strip() else None
                    count_val = form_data.get(f'sld_module_count{i}_{j}_{k}')
                    module_count = int(count_val) if count_val and str(count_val).strip() else None
                    inverter['slds'].append({
                        'uid': form_data.get(f'sld_uid{i}_{j}_{k}'),
                        'inv': inv_val,
                        'mppt': mppt_val,
                        'string': string_val,
                        'orientation': orientation_val,
                        'tilt_angle': tilt_angle,
                        'module_wattage': module_wattage,
                        'module_count': module_count,
                    })
                    k += 1
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
    _total_cap = request.form.get('total_capacity')
    total_capacity = float(_total_cap) if _total_cap and str(_total_cap).strip() else None
    latitude = request.form.get('latitude') or None
    longitude = request.form.get('longitude') or None
    installation_mode = request.form.get('installation_mode') or None
    installation_env = request.form.get('installation_env') or None
    power_structure = request.form.get('power_structure') or None

    structured_phases = parse_site_form_data(request.form)

    with session_scope() as session:
        query1 = Site.create(session, region = region, name = name, address = address, company = company, build_date = None if build_date == '' else build_date, wait_cheack = wait_cheack, phase_number = phase_number, user_uid = user_uid, total_capacity = total_capacity, latitude = latitude, longitude = longitude, installation_mode = installation_mode, installation_env = installation_env, power_structure = power_structure)
        for p_data in structured_phases:
            query2 = SitePhase.create(session, site_uid = query1.uid,  name = p_data['name'], sort = p_data['sort'], taipower_rate = p_data.get('taipower_rate'), greenpower_rate = p_data.get('greenpower_rate'))
            for i_data in p_data['inverters']:
                inv_row = SitePhaseInverter.create(session, phase_uid=query2.uid, brand=i_data['brand'], model=i_data['model'])
                for sld_data in i_data.get('slds', []):
                    SitePhaseInverterSld.create(session, inverter_uid=inv_row.uid, inv=sld_data.get('inv'), mppt=sld_data.get('mppt'), string=sld_data.get('string'), orientation=sld_data.get('orientation'), tilt_angle=sld_data.get('tilt_angle'), module_wattage=sld_data.get('module_wattage'), module_count=sld_data.get('module_count'))
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
            _gr = form_data.get(f'phase_greenpower_rate{i}')
            phase_obj = {'uid': form_data.get(f'phase_uid{i}'), 'name': form_data.get(f'phase_name{i}'), 'taipower_rate': float(_tr) if _tr and str(_tr).strip() else None, 'greenpower_rate': float(_gr) if _gr and str(_gr).strip() else None, 'inverters': [],'modules': [], 'sort': i}
            while True:
                brand_key = f'inverter_brand{i}_{j}'
                if brand_key not in form_data: break
                inverter = {'uid': form_data.get(f'inverter_uid{i}_{j}'), 'brand': form_data.get(f'inverter_brand{i}_{j}'), 'model': form_data.get(f'inverter_model{i}_{j}'), 'slds': []}
                sld_idx = 1
                while f'sld_inv{i}_{j}_{sld_idx}' in form_data:
                    tilt_val = form_data.get(f'sld_tilt_angle{i}_{j}_{sld_idx}')
                    watt_val = form_data.get(f'sld_module_wattage{i}_{j}_{sld_idx}')
                    count_val = form_data.get(f'sld_module_count{i}_{j}_{sld_idx}')
                    inverter['slds'].append({
                        'uid': form_data.get(f'sld_uid{i}_{j}_{sld_idx}'),
                        'inv': form_data.get(f'sld_inv{i}_{j}_{sld_idx}'),
                        'mppt': form_data.get(f'sld_mppt{i}_{j}_{sld_idx}'),
                        'string': form_data.get(f'sld_string{i}_{j}_{sld_idx}'),
                        'orientation': form_data.get(f'sld_orientation{i}_{j}_{sld_idx}'),
                        'tilt_angle': float(tilt_val) if tilt_val and str(tilt_val).strip() else None,
                        'module_wattage': float(watt_val) if watt_val and str(watt_val).strip() else None,
                        'module_count': int(count_val) if count_val and str(count_val).strip() else None,
                    })
                    sld_idx += 1
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
    _total_cap = request.form.get('total_capacity')
    total_capacity = float(_total_cap) if _total_cap and str(_total_cap).strip() else None
    latitude = request.form.get('latitude') or None
    longitude = request.form.get('longitude') or None
    installation_mode = request.form.get('installation_mode') or None
    installation_env = request.form.get('installation_env') or None
    power_structure = request.form.get('power_structure') or None

    structured_phases = parse_site_form_data(request.form)
    with session_scope() as session:
        Site.update(session, uid = site_uid, name = name, address = address, company = company, build_date = None if build_date == '' else build_date, wait_cheack = wait_cheack, total_capacity = total_capacity, latitude = latitude, longitude = longitude, installation_mode = installation_mode, installation_env = installation_env, power_structure = power_structure)
        stmt = delete(SitePhase).where(SitePhase.site_uid == site_uid)
        result = session.execute(stmt)
        for p_data in structured_phases:
            site_phase = SitePhase.create(session, site_uid = site_uid,  name = p_data['name'],  sort = p_data['sort'], taipower_rate = p_data.get('taipower_rate'), greenpower_rate = p_data.get('greenpower_rate'))
            for i_data in p_data['inverters']:
                inv_row = SitePhaseInverter.create(session, phase_uid=site_phase.uid, brand=i_data['brand'], model=i_data['model'])
                for sld_data in i_data.get('slds', []):
                    SitePhaseInverterSld.create(session, inverter_uid=inv_row.uid, inv=sld_data.get('inv'), mppt=sld_data.get('mppt'), string=sld_data.get('string'), orientation=sld_data.get('orientation'), tilt_angle=sld_data.get('tilt_angle'), module_wattage=sld_data.get('module_wattage'), module_count=sld_data.get('module_count'))
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