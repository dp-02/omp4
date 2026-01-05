from flask import Blueprint, render_template
from app.auth import login_required
blueprint = Blueprint('view_admin_dashboard', __name__)

@blueprint.route('/')
@login_required
def index():
    ''' 首頁 '''
    return render_template('adminDashboard/index.html')

@blueprint.route('/create/')
def create():
    ''' 新增使用者 '''
    return render_template('adminDashboard/form.html', act="create")
