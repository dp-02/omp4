from flask import Blueprint, request, make_response, url_for, render_template
from app.database import session_scope
from sqlalchemy import select, delete
from app.auth import login_required
import json
from app.models import Guest, Site

blueprint = Blueprint('api_guest_manager', __name__)

@blueprint.route('/partials/get_guest_rows', methods=['GET'])
@login_required
def get_guest_rows():
    ''' 取得訪客列表 HTML 行 '''
    guest_data = []
    with session_scope() as session:
        stmt = select(Guest, Site).outerjoin(Site, Guest.site_uid == Site.uid).order_by(Guest.uid.desc())
        results = session.execute(stmt).all()
        for g, s in results:
            item = Guest.to_dict(g)
            item['site_name'] = s.name if s else "尚未綁定"
            guest_data.append(item)
    return render_template('guestManager/partials/_guest_rows.html', guest_data=guest_data)

@blueprint.route('/partials/get_sites_by_region', methods=['GET'])
@login_required
def get_sites_by_region():
    ''' 取得特定地區的案場 HTML 選項 '''
    region_index = request.args.get('region_index', type=int)
    selected_site_uid = request.args.get('selected_site_uid', type=int)
    
    if region_index:
        with session_scope() as session:
            stmt = select(Site).where(Site.region == region_index).order_by(Site.name)
            sites = session.scalars(stmt).all()
            return render_template('guestManager/partials/_site_options.html', sites=sites, selected_site_uid=selected_site_uid)
            
    return render_template('guestManager/partials/_site_options.html', sites=[], selected_site_uid=selected_site_uid)

@blueprint.route('/create', methods=['POST'])
@login_required
def guest_create():
    ''' 建立訪客 '''
    account = request.form.get('account')
    password = request.form.get('password')
    site_uid = request.form.get('site_uid')
    
    with session_scope() as session:
        Guest.create(
            session,
            account=account,
            password=password,
            site_uid=site_uid if site_uid else None
        )
        
    response = make_response()
    trigger_data = {
        "response-data": {
            "title": "新增成功！",
            "text": "訪客帳號已建立，即將跳轉...",
            "redirectUrl": url_for('view_guest_manager.index')
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    return response

@blueprint.route('/update', methods=['POST'])
@login_required
def guest_update():
    ''' 更新訪客 '''
    uid = request.form.get('uid')
    account = request.form.get('account')
    password = request.form.get('password')
    site_uid = request.form.get('site_uid')
    
    with session_scope() as session:
        Guest.update(
            session,
            uid=uid,
            account=account,
            password=password,
            site_uid=site_uid if site_uid else None
        )
        
    response = make_response()
    trigger_data = {
        "response-data": {
            "title": "更新成功！",
            "text": "訪客帳號已更新，即將跳轉...",
            "redirectUrl": url_for('view_guest_manager.index')
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    return response

@blueprint.route('/delete/<int:uid>', methods=['DELETE'])
@login_required
def guest_delete(uid):
    ''' 刪除訪客 '''
    with session_scope() as session:
        Guest.delete(session, uid=uid)
    
    response = make_response()
    trigger_data = {
        "showToast": {
            "type": "success",
            "message": "已成功刪除該訪客"
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    return response, 200
