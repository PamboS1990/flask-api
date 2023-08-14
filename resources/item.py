from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt

from schemas import ItemSchema, ItemUpdateSchema, TagAndItemSchema
from models import ItemModel, ItemTagsModel
from db import db
from sqlalchemy.exc import SQLAlchemyError

from utils import check_admin_access

blp = Blueprint("Items", __name__, description="Operations on items.")


@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item
    
    @jwt_required(fresh=True)
    def delete(self, item_id):
        check_admin_access(jwt=get_jwt())
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted."}
    
    @jwt_required(fresh=True)
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
            item.store_id = item_data["store_id"]
        else:
            item = ItemModel(id=item_id, **item_data)
        
        db.session.add(item)
        db.session.commit()
        
        return item


@blp.route("/item")
class ItemList(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()
    
    @jwt_required(fresh=True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"{str(e)} - An error occurred while inserting the item.")
        return item


@blp.route("/itemtags")
class ItemTagList(MethodView):
    @blp.response(200, TagAndItemSchema(many=True))
    def get(self):
        return ItemTagsModel.query.all()
