from flask import Flask
from .adminDashboard import blueprint as adminDashboard
from .checklist import blueprint as checklist
from .construction import blueprint as construction
from .design import blueprint as design
from .download import blueprint as download
from .guest import blueprint as guest
from .home import blueprint as home
from .site import blueprint as site
from .guestManager import blueprint as guestManager

def init(app:Flask):
    app.register_blueprint(adminDashboard, url_prefix= '/adminDashboard')
    app.register_blueprint(checklist, url_prefix= '/checklist')
    app.register_blueprint(construction, url_prefix= '/construction')
    app.register_blueprint(design, url_prefix= '/design')
    app.register_blueprint(download, url_prefix= '/download')
    app.register_blueprint(guest, url_prefix='/guest')
    app.register_blueprint(home)
    app.register_blueprint(site, url_prefix= '/site')
    app.register_blueprint(guestManager, url_prefix= '/guestManager')