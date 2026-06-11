from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='tourist') # 'tourist' or 'owner'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Homestay(db.Model):
    __tablename__ = 'homestays'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False, default=2)
    amenities = db.Column(db.String(300), nullable=False) # comma-separated: "WiFi, Hot Water, Kitchen"
    eco_features = db.Column(db.String(300), nullable=False) # comma-separated: "Solar Power, Organic Garden, Zero Waste"
    image_url = db.Column(db.String(500), nullable=True)
    average_rating = db.Column(db.Float, default=0.0)

    # Relationships
    owner = db.relationship('User', backref=db.backref('homestays', lazy=True))
    activities = db.relationship('LocalActivity', backref='homestay', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='homestay', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else 'Unknown',
            'name': self.name,
            'location': self.location,
            'description': self.description,
            'price_per_night': self.price_per_night,
            'max_guests': self.max_guests,
            'amenities': [a.strip() for a in self.amenities.split(',')] if self.amenities else [],
            'eco_features': [e.strip() for e in self.eco_features.split(',')] if self.eco_features else [],
            'image_url': self.image_url,
            'average_rating': round(self.average_rating, 1) if self.average_rating else 0.0,
            'activities': [activity.to_dict() for activity in self.activities]
        }

class LocalActivity(db.Model):
    __tablename__ = 'local_activities'
    id = db.Column(db.Integer, primary_key=True)
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestays.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'Trekking', 'Farming', 'Cooking', 'Crafts', etc.
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'homestay_id': self.homestay_id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'price': self.price
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestays.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_guests = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'confirmed', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tourist = db.relationship('User', backref=db.backref('bookings', lazy=True))
    homestay = db.relationship('Homestay', backref=db.backref('bookings', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'tourist_id': self.tourist_id,
            'tourist_name': self.tourist.name if self.tourist else 'Unknown',
            'homestay_id': self.homestay_id,
            'homestay_name': self.homestay.name if self.homestay else 'Unknown',
            'homestay_location': self.homestay.location if self.homestay else 'Unknown',
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
            'total_guests': self.total_guests,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestays.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float, default=0.0) # -1.0 to 1.0
    sentiment_label = db.Column(db.String(20), default='neutral') # 'positive', 'neutral', 'negative'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tourist = db.relationship('User', backref=db.backref('reviews', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'tourist_name': self.tourist.name if self.tourist else 'Anonymous',
            'homestay_id': self.homestay_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
