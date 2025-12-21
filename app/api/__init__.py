from flask import Flask
from .adminDashboard import blueprint as adminDashboard
from .checklist import blueprint as checklist
from .construction import blueprint as construction
from .design import blueprint as design
from .site import blueprint as site

def init(app:Flask):
    app.register_blueprint(adminDashboard, url_prefix= '/api/adminDashboard')
    app.register_blueprint(checklist, url_prefix= '/api/checklist')
    app.register_blueprint(construction, url_prefix= '/api/construction')
    app.register_blueprint(design, url_prefix= '/api/design')
    app.register_blueprint(site, url_prefix= '/api/site')