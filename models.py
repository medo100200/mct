from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(100), unique=True, nullable=False)
    device_type = db.Column(db.String(100))
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    issue = db.Column(db.Text)
    inclusions = db.Column(db.Text)  # مشتملات الجهاز
    status = db.Column(db.String(50), default="قيد الإصلاح")
    cost = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    received_date = db.Column(db.String(50))
    delivered_date = db.Column(db.String(50))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin أو user
    approved = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
