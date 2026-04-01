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
    return render_template('guestManager/form.html', act='create', regions=region_map, data={})

@blueprint.route('/edit/<int:uid>/')
@login_required
def edit(uid):
    ''' 編輯訪客頁面 '''
    with session_scope() as session:
        guest = Guest.get(session, uid=uid)
        if not guest:
            return abort(404)
        form_data = Guest.to_dict(guest)
        
        # 查詢此訪客對應的案場所屬地區
        region_index = None
        if guest.site_uid:
            site = Site.get(session, uid=guest.site_uid)
            if site:
                region_index = site.region
                
        # 取得該地區的所有案場
        sites = []
        if region_index:
            stmt = select(Site).where(Site.region == region_index).order_by(Site.name)
            sites = session.scalars(stmt).all()
            
    return render_template('guestManager/form.html', 
                           act='update', 
                           regions=region_map, 
                           data=form_data, 
                           region_index=region_index,
                           sites=sites)
