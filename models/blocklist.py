from db import db


class BlockListModel(db.Model):
    __tablename__ = "blocklist"
    
    jti = db.Column(db.String(200), primary_key=True)
    