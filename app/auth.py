from flask import session, redirect, url_for
from functools import wraps

def login_required(f):
    ''' 登入驗證 '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_uid' not in session:
            return redirect(url_for('view_home.choose_user'))
        return f(*args, **kwargs)
    return decorated_function