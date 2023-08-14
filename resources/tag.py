from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

from utils import check_admin_access

blp = Blueprint("Tags", __name__, description="Operations on tags.")


@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()
    
    @jwt_required(fresh=True)
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort(400, message="A tag with that name already exists in that store.")
        if not StoreModel.query.filter(StoreModel.id == store_id).first():
            abort(404, message="The store you are trying to add a tag to doesn't exist.")
        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the tag.")
        return tag


@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @jwt_required(fresh=True)
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")
            
        return tag
    
    @jwt_required(fresh=True)
    @blp.response(200, TagAndItemSchema)
    @blp.alt_response(
        400,
        description="Returned if the tag and item are not from the same store.")
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        if item.store.id != tag.store.id:
            abort(400, message="Make sure item and tag belong to the same store before linking.")
        
        item.tags.remove(tag)
        
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"An error occurred while removing the tag. {e}")
            
        return {"message": "Item removed from tag", "item": item, "tag": tag}
    

@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    
    @jwt_required(fresh=True)
    @blp.response(
        202,
        description="Deletes a tag if no item is linked with it.",
        example={"message": "Tag deleted."})
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(
        400,
        description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.")
    def delete(self, tag_id):
        check_admin_access(jwt=get_jwt())
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "tag deleted."}
        abort(400,
              message="Could not delete tag. Make sure tag is not associated with any items then try again.")


@blp.route("/tag")
class TagList(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self):
        return TagModel.query.all()
