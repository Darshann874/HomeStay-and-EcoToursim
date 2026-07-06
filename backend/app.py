import os
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from database import db, User, Homestay, LocalActivity, Booking, Review
from datetime import datetime, date
from ml_engine import RecommendationEngine, SentimentAnalyzer, DemandPredictor, TravelChatbot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'eco-homestay-super-secret-key-12345')

# Database configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # SQLAlchemy requires 'postgresql://' instead of 'postgres://' which some cloud providers output
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Use local SQLite database as fallback
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eco_tourism.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for frontend integration
CORS(app, supports_credentials=True)

# Initialize database
db.init_app(app)

# Initialize ML engines
recommender = RecommendationEngine()
sentiment_analyzer = SentimentAnalyzer()
demand_predictor = DemandPredictor()
chatbot = TravelChatbot()

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Default index route
@app.route('/')
def home():
    return render_template('index.html')

# Helper: parse date from string
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return None

# -----------------
# Auth Endpoints
# -----------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'tourist') # 'tourist' or 'owner'

    if not name or not email or not password:
        return jsonify({'error': 'All fields (name, email, password) are required.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered.'}), 400

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'Registration successful.', 'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session['user_id'] = user.id
    session['user_role'] = user.role
    
    return jsonify({
        'message': 'Login successful.',
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        # Check Authorization header as fallback if cookies aren't stored
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                uid = int(auth_header.split(' ')[1])
                user = User.query.get(uid)
                if user:
                    return jsonify({'user': user.to_dict()}), 200
            except ValueError:
                pass
        return jsonify({'user': None}), 200
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'user': None}), 200
        
    return jsonify({'user': user.to_dict()}), 200

# -----------------
# Homestay Endpoints
# -----------------
@app.route('/api/homestays', methods=['GET'])
def get_homestays():
    location = request.args.get('location')
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    eco_feature = request.args.get('eco_feature')
    search_query = request.args.get('search')

    query = Homestay.query

    if location:
        query = query.filter(Homestay.location.ilike(f'%{location}%'))
    if max_price:
        query = query.filter(Homestay.price_per_night <= max_price)
    if min_rating:
        query = query.filter(Homestay.average_rating >= min_rating)
    if search_query:
        query = query.filter(
            db.or_(
                Homestay.name.ilike(f'%{search_query}%'),
                Homestay.description.ilike(f'%{search_query}%'),
                Homestay.location.ilike(f'%{search_query}%')
            )
        )

    homestays = query.all()

    # Manual list filter for comma-separated fields
    if eco_feature:
        homestays = [h for h in homestays if any(eco_feature.lower() in f.lower() for f in (h.eco_features.split(',') if h.eco_features else []))]

    return jsonify([h.to_dict() for h in homestays]), 200

@app.route('/api/homestays/<int:homestay_id>', methods=['GET'])
def get_homestay_details(homestay_id):
    homestay = Homestay.query.get_or_4_none(homestay_id)
    if not homestay:
        return jsonify({'error': 'Homestay not found.'}), 404
        
    # Get reviews for this homestay
    reviews = Review.query.filter_by(homestay_id=homestay_id).order_by(Review.created_at.desc()).all()
    
    res = homestay.to_dict()
    res['reviews'] = [r.to_dict() for r in reviews]
    return jsonify(res), 200

@app.route('/api/homestays', methods=['POST'])
def create_homestay():
    # Retrieve data
    data = request.get_json() or {}
    owner_id = data.get('owner_id') or session.get('user_id')
    
    if not owner_id:
        return jsonify({'error': 'Unauthorized. Please login as a homestay owner.'}), 401
        
    owner = User.query.get(owner_id)
    if not owner or owner.role != 'owner':
        return jsonify({'error': 'Only registered owners can create homestay listings.'}), 403

    name = data.get('name')
    location = data.get('location')
    description = data.get('description')
    price_per_night = data.get('price_per_night')
    max_guests = data.get('max_guests', 2)
    amenities = data.get('amenities', '')
    eco_features = data.get('eco_features', '')
    image_url = data.get('image_url')

    if not name or not location or not description or not price_per_night:
        return jsonify({'error': 'Name, location, description, and price are required.'}), 400

    homestay = Homestay(
        owner_id=owner_id,
        name=name,
        location=location,
        description=description,
        price_per_night=float(price_per_night),
        max_guests=int(max_guests),
        amenities=amenities,
        eco_features=eco_features,
        image_url=image_url or "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80"
    )

    try:
        db.session.add(homestay)
        db.session.commit()
        return jsonify({'message': 'Homestay listed successfully.', 'homestay': homestay.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/homestays/<int:homestay_id>/activities', methods=['POST'])
def add_activity(homestay_id):
    data = request.get_json() or {}
    name = data.get('name')
    act_type = data.get('type')
    description = data.get('description')
    price = data.get('price', 0.0)

    if not name or not act_type or not description:
        return jsonify({'error': 'Name, type, and description are required.'}), 400

    homestay = Homestay.query.get(homestay_id)
    if not homestay:
        return jsonify({'error': 'Homestay not found.'}), 404

    activity = LocalActivity(
        homestay_id=homestay_id,
        name=name,
        type=act_type,
        description=description,
        price=float(price)
    )

    try:
        db.session.add(activity)
        db.session.commit()
        return jsonify({'message': 'Activity added successfully.', 'activity': activity.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# -----------------
# Booking Endpoints
# -----------------
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    tourist_id = data.get('tourist_id') or session.get('user_id')
    homestay_id = data.get('homestay_id')
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')
    total_guests = data.get('total_guests', 1)

    if not tourist_id:
        return jsonify({'error': 'Unauthorized. Please login as a tourist.'}), 401
        
    if not homestay_id or not check_in_str or not check_out_str:
        return jsonify({'error': 'Homestay ID, check-in, and check-out dates are required.'}), 400

    homestay = Homestay.query.get(homestay_id)
    if not homestay:
        return jsonify({'error': 'Homestay not found.'}), 404

    check_in = parse_date(check_in_str)
    check_out = parse_date(check_out_str)

    if not check_in or not check_out:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        
    if check_in >= check_out:
        return jsonify({'error': 'Check-out date must be after check-in date.'}), 400

    duration = (check_out - check_in).days
    total_price = homestay.price_per_night * duration * int(total_guests)

    booking = Booking(
        tourist_id=tourist_id,
        homestay_id=homestay_id,
        check_in=check_in,
        check_out=check_out,
        total_guests=int(total_guests),
        total_price=total_price,
        status='pending'
    )

    try:
        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Booking requested successfully.', 'booking': booking.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    user_id = request.args.get('user_id', type=int) or session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized.'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if user.role == 'owner':
        # Get bookings for all homestays owned by this owner
        bookings = Booking.query.join(Homestay).filter(Homestay.owner_id == user_id).order_by(Booking.created_at.desc()).all()
    else:
        # Get bookings made by this tourist
        bookings = Booking.query.filter_by(tourist_id=user_id).order_by(Booking.created_at.desc()).all()

    return jsonify([b.to_dict() for b in bookings]), 200

@app.route('/api/bookings/<int:booking_id>/status', methods=['PUT'])
def update_booking_status(booking_id):
    data = request.get_json() or {}
    status = data.get('status') # 'confirmed', 'cancelled', 'completed'

    if not status or status not in ['confirmed', 'cancelled', 'completed', 'pending']:
        return jsonify({'error': 'Invalid status provided.'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found.'}), 404

    booking.status = status
    try:
        db.session.commit()
        return jsonify({'message': f'Booking status updated to {status}.', 'booking': booking.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# -----------------
# Reviews & Sentiment Endpoints
# -----------------
@app.route('/api/reviews', methods=['POST'])
def create_review():
    data = request.get_json() or {}
    tourist_id = data.get('tourist_id') or session.get('user_id')
    homestay_id = data.get('homestay_id')
    rating = data.get('rating')
    review_text = data.get('review_text')

    if not tourist_id:
        return jsonify({'error': 'Unauthorized. Please log in to leave reviews.'}), 401

    if not homestay_id or not rating or not review_text:
        return jsonify({'error': 'Homestay ID, rating, and review text are required.'}), 400

    homestay = Homestay.query.get(homestay_id)
    if not homestay:
        return jsonify({'error': 'Homestay not found.'}), 404

    # Run AI Sentiment Analysis
    sentiment_score, sentiment_label = sentiment_analyzer.analyze(review_text)

    review = Review(
        tourist_id=tourist_id,
        homestay_id=homestay_id,
        rating=int(rating),
        review_text=review_text,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label
    )

    try:
        db.session.add(review)
        db.session.commit()

        # Recalculate homestay average rating
        reviews = Review.query.filter_by(homestay_id=homestay_id).all()
        homestay.average_rating = sum(r.rating for r in reviews) / len(reviews)
        db.session.commit()

        return jsonify({'message': 'Review submitted.', 'review': review.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# -----------------
# AI recommendation endpoint
# -----------------
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    pref_query = request.args.get('preferences', '')
    homestays = Homestay.query.all()
    
    if not pref_query or len(pref_query.strip()) == 0:
        # If no preferences, return highest rated
        homestays_sorted = sorted(homestays, key=lambda x: x.average_rating, reverse=True)
        return jsonify([{**h.to_dict(), 'score': 1.0} for h in homestays_sorted]), 200
        
    scored_list = recommender.recommend(pref_query, homestays)
    
    result = []
    for h, score in scored_list:
        h_dict = h.to_dict()
        h_dict['score'] = round(score, 3)
        result.append(h_dict)
        
    return jsonify(result), 200

# -----------------
# Chatbot Endpoints
# -----------------
@app.route('/api/chatbot', methods=['POST'])
def post_chatbot():
    data = request.get_json() or {}
    message = data.get('message')
    reply = chatbot.get_reply(message)
    return jsonify({'reply': reply}), 200

# -----------------
# Owner Analytics Dashboard Endpoint
# -----------------
@app.route('/api/owner/analytics', methods=['GET'])
def get_owner_analytics():
    owner_id = request.args.get('owner_id', type=int) or session.get('user_id')
    if not owner_id:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    owner = User.query.get(owner_id)
    if not owner or owner.role != 'owner':
        return jsonify({'error': 'Unauthorized. Host access only.'}), 403

    homestays = Homestay.query.filter_by(owner_id=owner_id).all()
    homestay_ids = [h.id for h in homestays]

    if not homestay_ids:
        return jsonify({
            'total_bookings': 0,
            'total_revenue': 0.0,
            'monthly_revenue': [],
            'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
            'demand_predictions': {}
        }), 200

    # 1. Total & Monthly Revenue
    completed_bookings = Booking.query.filter(
        Booking.homestay_id.in_(homestay_ids), 
        Booking.status == 'completed'
    ).all()
    
    total_revenue = sum(b.total_price for b in completed_bookings)
    total_bookings = len(completed_bookings)

    # Monthly revenue aggregation for chart
    monthly_data = {}
    for b in completed_bookings:
        month_name = b.check_in.strftime('%Y-%m') # E.g. "2026-05"
        monthly_data[month_name] = monthly_data.get(month_name, 0.0) + b.total_price

    # Sort monthly revenue
    sorted_months = sorted(monthly_data.keys())
    monthly_revenue_list = [{'month': m, 'revenue': monthly_data[m]} for m in sorted_months]

    # 2. Sentiment Breakdown of Reviews
    reviews = Review.query.filter(Review.homestay_id.in_(homestay_ids)).all()
    sentiment_breakdown = {'positive': 0, 'neutral': 0, 'negative': 0}
    for r in reviews:
        label = r.sentiment_label or 'neutral'
        sentiment_breakdown[label] = sentiment_breakdown.get(label, 0) + 1

    # 3. AI Demand prediction for the next 6 months for each homestay
    demand_predictions = {}
    current_month = datetime.now().month
    for h in homestays:
        homestay_forecasts = []
        for offset in range(1, 7):
            pred_month = (current_month + offset - 1) % 12 + 1
            predicted_occ = demand_predictor.predict_occupancy(
                month=pred_month,
                location=h.location,
                price=h.price_per_night,
                rating=h.average_rating
            )
            month_label = datetime(2026, pred_month, 1).strftime('%B')
            homestay_forecasts.append({
                'month': month_label,
                'occupancy': round(predicted_occ, 1)
            })
        demand_predictions[h.name] = homestay_forecasts

    return jsonify({
        'total_bookings': total_bookings,
        'total_revenue': round(total_revenue, 2),
        'monthly_revenue': monthly_revenue_list,
        'sentiment_breakdown': sentiment_breakdown,
        'demand_predictions': demand_predictions
    }), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
