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
        from app.models import GuestSite
        stmt = select(Guest).order_by(Guest.uid.desc())
        results = session.execute(stmt).scalars().all()
        for g in results:
            item = Guest.to_dict(g)
            guest_sites = session.execute(select(Site.name).join(GuestSite, GuestSite.site_uid == Site.uid).where(GuestSite.guest_uid == g.uid)).scalars().all()
            if guest_sites:
                item['site_name'] = "、".join(guest_sites)
            else:
                item['site_name'] = "尚未綁定"
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
    site_uids = request.form.getlist('site_uids')
    
    with session_scope() as session:
        new_guest = Guest.create(
            session,
            account=account,
            password=password
        )
        if site_uids:
            from app.models import GuestSite
            for s_uid in site_uids:
                GuestSite.create(session, guest_uid=new_guest.uid, site_uid=s_uid)
        
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
    site_uids = request.form.getlist('site_uids')
    
    with session_scope() as session:
        Guest.update(
            session,
            uid=uid,
            account=account,
            password=password
        )
        from app.models import GuestSite
        session.execute(delete(GuestSite).where(GuestSite.guest_uid == uid))
        if site_uids:
            for s_uid in site_uids:
                GuestSite.create(session, guest_uid=uid, site_uid=s_uid)
        
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
        from app.models import GuestSite
        session.execute(delete(GuestSite).where(GuestSite.guest_uid == uid))
    
    response = make_response()
    trigger_data = {
        "showToast": {
            "type": "success",
            "message": "已成功刪除該訪客"
        }
    }
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    return response, 200
