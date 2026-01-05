from app import create_app
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app()

if __name__ == '__main__':
    # 如果 ENV 是 'production'，則執行生產模式
    if app.config.get('FLASK_DEBUG') == '0':
        print("🚀 Starting Production Server (Waitress)...")
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        host = app.config.get('PROD_HOST', '0.0.0.0')
        port = app.config.get('PROD_PORT', 8000)
        serve(app, host=host, port=port)
    else:
        print("🛠 Starting Development Server...")
        app.run(debug=True)