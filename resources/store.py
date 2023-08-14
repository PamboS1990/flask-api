from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt

from schemas import StoreSchema
from db import db
from models import StoreModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from utils import check_admin_access

blp = Blueprint("Stores", __name__, description="Operations on stores.")


@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store
    
    @jwt_required(fresh=True)
    def delete(self, store_id):
        check_admin_access(jwt=get_jwt())
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted."}, 200


@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()
    
    @jwt_required(fresh=True)
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exists.")
        except SQLAlchemyError:
            abort(500,  message="An error occurred while inserting the store.")
        return store
