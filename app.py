import os

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from db import db
import models
from models import BlockListModel

from resources.item import blp as item_blueprint
from resources.store import blp as store_blueprint
from resources.tag import blp as tag_blueprint
from resources.user import blp as user_blueprint


def create_app(db_url=None):
    app = Flask(__name__)
    
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    migrate = Migrate(app, db)
    api = Api(app)
    
    # TODO move to env variable
    app.config["JWT_SECRET_KEY"] = "282666708968075320339636279668288743076"
    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        """
        Checks if the token is in the blocklist. Blocks request if it returns True.
        
        :param jwt_header:
        :param jwt_payload:
        :return:
        """
        jti = jwt_payload["jti"]
        if BlockListModel.query.filter(BlockListModel.jti == jti).first():
            return True
        else:
            return False
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """
        The message that is returned when a token is revoked.
        
        :param jwt_header:
        :param jwt_payload:
        :return:
        """
        return jsonify({"description": "The token has been revoked.", "error": "token_revoked"}), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            "description": "The token is not fresh",
            "error": "fresh_token_required"
        }), 401
    
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        # TODO lookup in db
        if identity == 1:
            return {"is_admin": True}
        else:
            return {"is_admin": False}
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has expired.",
                        "error": "token_Expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Signature verification failed.",
                        "error": "invalid_token"}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"description": "request does not contain an access token.",
                        "error": "authorization_required"}), 401
    
    # with app.app_context():
    #     db.create_all()
    
    api.register_blueprint(item_blueprint)
    api.register_blueprint(store_blueprint)
    api.register_blueprint(tag_blueprint)
    api.register_blueprint(user_blueprint)
    
    return app
