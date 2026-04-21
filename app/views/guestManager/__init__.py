from flask import Blueprint, render_template, abort
from app.database import session_scope
from app.auth import login_required
from sqlalchemy import select
from app.models import Guest, Site

blueprint = Blueprint('view_guest_manager', __name__)

region_map = {
    1: "北部",
    2: "中彰投",
    3: "雲嘉南",
    4: "高屏",
    5: "東部"
}

@blueprint.route('/')
@login_required
def index():
    ''' 訪客管理列表頁 '''
    return render_template('guestManager/index.html')

@blueprint.route('/create/')
@login_required
def create():
    ''' 新增訪客頁面 '''
    with session_scope() as session:
        sites = session.scalars(select(Site).order_by(Site.region, Site.name)).all()
    return render_template('guestManager/form.html', act='create', regions=region_map, data={}, sites=sites)

@blueprint.route('/edit/<int:uid>/')
@login_required
def edit(uid):
    ''' 編輯訪客頁面 '''
    with session_scope() as session:
        guest = Guest.get(session, uid=uid)
        if not guest:
            return abort(404)
        form_data = Guest.to_dict(guest)
        
        # 取得此訪客關聯的案場 UIDs
        from app.models import GuestSite
        guest_sites = session.scalars(select(GuestSite.site_uid).where(GuestSite.guest_uid == uid)).all()
        form_data['site_uids'] = guest_sites
        
        # 取得所有案場
        sites = session.scalars(select(Site).order_by(Site.region, Site.name)).all()
            
    return render_template('guestManager/form.html', 
                           act='update', 
                           regions=region_map, 
                           data=form_data, 
                           sites=sites)
