from flask import Flask, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.client import client_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(client_bp, url_prefix='/client')

    @app.context_processor
    def inject_ui_context():
        from flask_login import current_user

        is_admin = current_user.is_authenticated and current_user.is_admin
        is_client = current_user.is_authenticated and not current_user.is_admin

        nav_sections = []
        quick_actions = []

        if is_admin:
            nav_sections = [
                {
                    'title': 'Overview',
                    'links': [
                        {'endpoint': 'admin.dashboard', 'label': 'Dashboard', 'icon': '◌'},
                    ],
                },
                {
                    'title': 'Commerce',
                    'links': [
                        {'endpoint': 'admin.products', 'label': 'Products', 'icon': '▣'},
                        {'endpoint': 'admin.categories', 'label': 'Categories', 'icon': '▢'},
                        {'endpoint': 'admin.suppliers', 'label': 'Suppliers', 'icon': '◫'},
                        {'endpoint': 'admin.orders', 'label': 'Orders', 'icon': '↗'},
                        {'endpoint': 'admin.deliveries', 'label': 'Deliveries', 'icon': '⟡'},
                        {'endpoint': 'admin.list_devis', 'label': 'Quotes', 'icon': '⌁'},
                    ],
                },
            ]
            quick_actions = [
                {'label': 'Open products', 'endpoint': 'admin.products', 'shortcut': 'G P'},
                {'label': 'Open orders', 'endpoint': 'admin.orders', 'shortcut': 'G O'},
                {'label': 'Open deliveries', 'endpoint': 'admin.deliveries', 'shortcut': 'G D'},
            ]
        elif is_client:
            nav_sections = [
                {
                    'title': 'Shopping',
                    'links': [
                        {'endpoint': 'client_bp.menu', 'label': 'Catalogue', 'icon': '◌'},
                        {'endpoint': 'client_bp.cart', 'label': 'Cart', 'icon': '▣'},
                        {'endpoint': 'client_bp.history', 'label': 'Orders', 'icon': '↗'},
                        {'endpoint': 'client_bp.my_devis', 'label': 'Quotes', 'icon': '⌁'},
                    ],
                },
            ]
            quick_actions = [
                {'label': 'Open catalogue', 'endpoint': 'client_bp.menu', 'shortcut': 'G M'},
                {'label': 'Open cart', 'endpoint': 'client_bp.cart', 'shortcut': 'G C'},
                {'label': 'Open orders', 'endpoint': 'client_bp.history', 'shortcut': 'G H'},
            ]
        else:
            nav_sections = [
                {
                    'title': 'Explore',
                    'links': [
                        {'endpoint': 'main.index', 'label': 'Home', 'icon': '◌'},
                        {'endpoint': 'client_bp.menu', 'label': 'Catalogue', 'icon': '▣'},
                    ],
                },
            ]
            quick_actions = [
                {'label': 'Go to home', 'endpoint': 'main.index', 'shortcut': 'G H'},
                {'label': 'Open catalogue', 'endpoint': 'client_bp.menu', 'shortcut': 'G M'},
            ]

        breadcrumb_map = {
            'main.index': [('Home', url_for('main.index'))],
            'auth.login': [('Authentication', None), ('Login', None)],
            'auth.register': [('Authentication', None), ('Sign up', None)],
            'client_bp.menu': [('Shop', None), ('Catalogue', None)],
            'client_bp.cart': [('Shop', None), ('Cart', None)],
            'client_bp.checkout': [('Shop', None), ('Checkout', None)],
            'client_bp.history': [('Account', None), ('Orders', None)],
            'client_bp.order_detail': [('Account', None), ('Order details', None)],
            'client_bp.my_devis': [('Account', None), ('Quotes', None)],
            'admin.dashboard': [('Administration', None), ('Dashboard', None)],
            'admin.products': [('Administration', None), ('Catalogue', None), ('Products', None)],
            'admin.categories': [('Administration', None), ('Catalogue', None), ('Categories', None)],
            'admin.suppliers': [('Administration', None), ('Catalogue', None), ('Suppliers', None)],
            'admin.orders': [('Administration', None), ('Operations', None), ('Orders', None)],
            'admin.deliveries': [('Administration', None), ('Operations', None), ('Deliveries', None)],
            'admin.list_devis': [('Administration', None), ('Operations', None), ('Quotes', None)],
        }

        breadcrumbs = breadcrumb_map.get(request.endpoint, [])
        if not breadcrumbs and request.endpoint:
            pretty = request.endpoint.split('.')[-1].replace('_', ' ').title()
            breadcrumbs = [('Home', url_for('main.index')), (pretty, None)]

        return {
            'ui_nav_sections': nav_sections,
            'ui_quick_actions': quick_actions,
            'ui_breadcrumbs': breadcrumbs,
            'ui_shell_admin': is_admin,
            'ui_shell_client': is_client,
        }

    return app
