from flask import Blueprint, render_template
from app.auth import login_required

blueprint = Blueprint('view_summary', __name__)

@blueprint.route('/')
@login_required
def index():
    ''' 統整頁面 '''
    return render_template('summary/index.html')
