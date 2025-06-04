from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config
from app.database import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    api = Api(app)
    
    # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Interim App API",
            "description": "API pour l'application de recherche d'emploi intérimaire",
            "version": "1.0.0"
        },
        "host": "localhost:5000",
        "basePath": "/api",
        "schemes": ["http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Initialize database
    init_db(app)
    
    # Register routes
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.companies import companies_bp
    from app.routes.jobs import jobs_bp
    from app.routes.applications import applications_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(companies_bp, url_prefix='/api/companies')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    
    @app.route('/')
    def home():
        return {
            'message': 'Bienvenue sur l\'API Interim App',
            'documentation': '/apidocs/',
            'status': 'Fonctionnel'
        }
    
    return app