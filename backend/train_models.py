import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to path so we can import models and db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db, User, Homestay, LocalActivity, Booking, Review
from app import app  # Import app to use its db context

# Setup directories
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

def train_sentiment_model():
    print("Training Sentiment Analysis Model...")
    
    # Synthetic reviews dataset
    reviews_data = [
        # Positive reviews
        ("Beautiful homestay, very clean and peaceful. Solar power was great!", "positive"),
        ("Amazing hospitality. The host cooked delicious organic local meals.", "positive"),
        ("Loved the farming experience. Very sustainable and zero waste.", "positive"),
        ("Wonderful view of the mountains. Highly recommend the trekking tour.", "positive"),
        ("Excellent service. Clean rooms and warm hot water. Peaceful nature around.", "positive"),
        ("Best eco stay ever. They recycle everything and use rainwater harvesting.", "positive"),
        ("Super cozy rooms, friendly staff, and great organic coffee.", "positive"),
        ("Highly recommend! A perfect combination of comfort and environment conservation.", "positive"),
        ("Beautiful garden, quiet environment, and extremely hospitable host.", "positive"),
        ("A fantastic place to relax and enjoy local culture. We loved the cooking class.", "positive"),
        
        # Neutral reviews
        ("The stay was okay. Rooms are decent but wifi was a bit slow.", "neutral"),
        ("Average experience. Nice location but price is slightly high.", "neutral"),
        ("Decent place. Food was good, but amenities were basic.", "neutral"),
        ("It was fine. Close to the market but a bit noisy in the evening.", "neutral"),
        ("Standard room. Clean enough but nothing extraordinary.", "neutral"),
        ("Good location, but limited hot water. Host was polite.", "neutral"),
        ("Average room, clean sheets. Basic stay for eco tourists.", "neutral"),
        ("Okay for a night. Pretty garden, but room was small.", "neutral"),
        ("Decent price, close to trekking starting point. Fairly clean.", "neutral"),
        ("Fine place, but booking check-in process took too long.", "neutral"),
        
        # Negative reviews
        ("Very dirty rooms and no hot water. Disappointing experience.", "negative"),
        ("The owner was very rude. Will not stay here again.", "negative"),
        ("Extremely expensive for such poor facilities. No solar power as claimed.", "negative"),
        ("Noisy environment and broken furniture. Terrible service.", "negative"),
        ("Bad smell in the bathroom. The food made us sick. Avoid this place.", "negative"),
        ("Horrible experience. The listing photos are fake. It is run down.", "negative"),
        ("Waste of money. Unfriendly staff and dirty beds.", "negative"),
        ("No internet, cold rooms, and power cuts. Very uncomfortable stay.", "negative"),
        ("Very poor hygiene. The kitchen was dirty. Disappointed.", "negative"),
        ("Felt unsafe. Remote location with no proper lighting at night.", "negative")
    ]
    
    # Double the dataset size with minor variations for better training
    expanded_reviews = []
    for text, label in reviews_data:
        expanded_reviews.append((text, label))
        # Add slight variations
        expanded_reviews.append((text + " " + ( "Enjoyed it." if label == "positive" else "It was alright." if label == "neutral" else "Dislike it." ), label))
        
    df = pd.DataFrame(expanded_reviews, columns=['text', 'sentiment'])
    
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    X = vectorizer.fit_transform(df['text'])
    y = df['sentiment']
    
    model = LogisticRegression(C=1.0, class_weight='balanced')
    model.fit(X, y)
    
    # Save the model
    with open(os.path.join(MODEL_DIR, 'sentiment_model.pkl'), 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'model': model}, f)
    print("Sentiment Analysis Model saved successfully.")

def train_demand_model():
    print("Training Demand Prediction Model...")
    
    # Generate synthetic demand dataset
    # Features: Month (1-12), Location Code, Price, Rating
    locations = ['himalayas', 'kerala backwaters', 'goa beach', 'rajasthan desert', 'western ghats']
    location_encoder = {loc: idx for idx, loc in enumerate(locations)}
    
    np.random.seed(42)
    n_samples = 1000
    
    months = np.random.randint(1, 13, size=n_samples)
    loc_indices = np.random.randint(0, len(locations), size=n_samples)
    prices = np.random.uniform(30.0, 200.0, size=n_samples)
    ratings = np.random.uniform(2.5, 5.0, size=n_samples)
    
    # Occupancy formula with logical rules:
    # - Peak occupancy in summer (May-July) and winter (Dec-Jan)
    # - Higher ratings = higher occupancy
    # - Higher price = lower occupancy
    # - Location seasonal differences (Himalayas high in summer, Goa high in winter)
    
    occupancies = []
    for i in range(n_samples):
        m = months[i]
        loc = loc_indices[i]
        p = prices[i]
        r = ratings[i]
        
        # Base occupancy
        occ = 40.0
        
        # Seasonal occupancy waves
        if m in [5, 6, 7]: # Summer peak
            occ += 25.0
        elif m in [12, 1]: # Winter peak
            occ += 20.0
        elif m in [4, 8, 9, 10]: # Mid season
            occ += 5.0
        else: # Low season
            occ -= 15.0
            
        # Rating boost
        occ += (r - 3.0) * 15.0
        
        # Price penalty
        occ -= (p - 80.0) * 0.15
        
        # Location specific modifications
        if loc == 0:  # Himalayas: extra boost in summer (May-July)
            if m in [5, 6, 7]:
                occ += 10.0
        elif loc == 2:  # Goa: extra boost in winter (Nov-Jan)
            if m in [11, 12, 1]:
                occ += 15.0
                
        # Add random noise
        occ += np.random.normal(0, 5.0)
        
        # Cap between 5% and 95%
        occ = max(5.0, min(95.0, occ))
        occupancies.append(occ)
        
    X = np.column_stack((months, loc_indices, prices, ratings))
    y = np.array(occupancies)
    
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    
    # Save the model
    with open(os.path.join(MODEL_DIR, 'demand_model.pkl'), 'wb') as f:
        pickle.dump({'model': model, 'location_encoder': location_encoder}, f)
    print("Demand Prediction Model saved successfully.")

def seed_database():
    print("Seeding database...")
    with app.app_context():
        # Recreate tables
        db.drop_all()
        db.create_all()
        
        # 1. Create Users (Owners and Tourists)
        owner1 = User(name="Rajesh Sharma", email="rajesh@example.com", role="owner")
        owner1.set_password("password123")
        
        owner2 = User(name="Devi Nair", email="devi@example.com", role="owner")
        owner2.set_password("password123")
        
        tourist1 = User(name="Alice Johnson", email="alice@example.com", role="tourist")
        tourist1.set_password("password123")
        
        tourist2 = User(name="Kabir Patel", email="kabir@example.com", role="tourist")
        tourist2.set_password("password123")
        
        db.session.add_all([owner1, owner2, tourist1, tourist2])
        db.session.commit() # Commit to get User IDs
        
        # 2. Create Eco-Homestays
        h1 = Homestay(
            owner_id=owner1.id,
            name="Himalayan Eco Ridge Retreat",
            location="Himalayas",
            description="Experience pristine mountain living in our wood-and-stone cottage. We run entirely on solar power, serve 100% organic meals from our backyard garden, and practice rainwater harvesting. Perfect for nature lovers, hikers, and writers looking for a peaceful sanctuary.",
            price_per_night=85.00,
            max_guests=4,
            amenities="WiFi, Heater, Kitchen, Hot Water, Mountain View",
            eco_features="Solar Power, Organic Garden, Rainwater Harvesting, Zero Waste",
            image_url="https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?auto=format&fit=crop&w=800&q=80",
            average_rating=4.8
        )
        
        h2 = Homestay(
            owner_id=owner2.id,
            name="Kerala Backwater Organic Farmstay",
            location="Kerala Backwaters",
            description="Live on a sustainable farm surrounded by tranquil waters. Enjoy traditional houses constructed with locally sourced bamboo and clay, solar-powered facilities, and explore our spice orchard. Canoe rides, farm harvesting, and traditional cooking lessons are all part of the experience.",
            price_per_night=70.00,
            max_guests=3,
            amenities="WiFi, Air Conditioning, Breakfast Included, Lake View",
            eco_features="Local Clay Architecture, Biogas Fuel, Organic Orchards, Plastic Free",
            image_url="https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=800&q=80",
            average_rating=4.9
        )
        
        h3 = Homestay(
            owner_id=owner1.id,
            name="Desert Solar Oasis",
            location="Rajasthan Desert",
            description="Discover the beauty of the desert in mud huts designed to stay cool naturally. Our solar field provides all electricity, and greywater is recycled to support local desert trees. Experience traditional folk music, night stargazing, and camel rides guided by local community members.",
            price_per_night=60.00,
            max_guests=2,
            amenities="Kitchen, Desert View, Traditional Decor, Fire Pit",
            eco_features="Solar Micro-Grid, Mud Wall Insulations, Greywater Recycling, Community-Led",
            image_url="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
            average_rating=4.5
        )
        
        h4 = Homestay(
            owner_id=owner2.id,
            name="Western Ghats Treehouse Canopy",
            location="Western Ghats",
            description="Nestled deep in the forest canopy, this eco-treehouse offers a close connection with nature. Built responsibly around living trees without harming them, we use low-impact solar lighting, compost toilets, and offer immersive biological trail tours to support forest conservation efforts.",
            price_per_night=120.00,
            max_guests=2,
            amenities="Forest View, Solar Lights, Balcony, Composting Toilet",
            eco_features="Tree-Friendly Design, Dry Composting, Low Impact Lighting, Wildlife Conservation Partner",
            image_url="https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=800&q=80",
            average_rating=4.7
        )

        db.session.add_all([h1, h2, h3, h4])
        db.session.commit() # Commit to get Homestay IDs
        
        # 3. Create Local Activities
        act1_1 = LocalActivity(
            homestay_id=h1.id,
            name="Guided Mountain Trekking",
            type="Trekking",
            description="A 4-hour guided trek up to a hidden ridge overlooking snow-capped peaks, led by a local Sherpa guide.",
            price=20.00
        )
        act1_2 = LocalActivity(
            homestay_id=h1.id,
            name="Himalayan Organic Cooking Class",
            type="Cooking",
            description="Harvest spinach, potatoes, and local herbs directly from our garden and learn to cook traditional momos and local dal.",
            price=15.00
        )
        act2_1 = LocalActivity(
            homestay_id=h2.id,
            name="Backwater Canoe Fishing",
            type="Farming",
            description="Row a traditional wooden canoe and learn indigenous fishing techniques using eco-friendly bamboo nets.",
            price=25.00
        )
        act2_2 = LocalActivity(
            homestay_id=h2.id,
            name="Spices & Coconut Weaving Workshop",
            type="Crafts",
            description="Tour the farm to learn about cardamoms, pepper, and coconut harvesting, followed by a coconut leaf weaving session.",
            price=10.00
        )
        act3_1 = LocalActivity(
            homestay_id=h3.id,
            name="Desert Stargazing & Folk Lore",
            type="Local Culture",
            description="Gather around the fire pit under the clear desert night sky to observe constellations and listen to historic folk stories.",
            price=12.00
        )
        
        db.session.add_all([act1_1, act1_2, act2_1, act2_2, act3_1])
        
        # 4. Add Reviews with Pre-evaluated Sentiments
        # Homestay 1 Reviews
        r1_1 = Review(
            tourist_id=tourist1.id,
            homestay_id=h1.id,
            rating=5,
            review_text="This was a beautiful homestay, very clean and peaceful. The solar energy worked flawlessly, and waking up to the mountain views was magical!",
            sentiment_score=0.9,
            sentiment_label="positive"
        )
        r1_2 = Review(
            tourist_id=tourist2.id,
            homestay_id=h1.id,
            rating=4,
            review_text="Host Rajesh is wonderful. The organic meals were healthy and fresh. Room was slightly cold at night, but the blankets were warm.",
            sentiment_score=0.65,
            sentiment_label="positive"
        )
        
        # Homestay 2 Reviews
        r2_1 = Review(
            tourist_id=tourist1.id,
            homestay_id=h2.id,
            rating=5,
            review_text="Absolutely loved the organic farm! The bamboo architecture was stunning and very cool. The local food cooked by Devi was outstanding.",
            sentiment_score=0.95,
            sentiment_label="positive"
        )
        r2_2 = Review(
            tourist_id=tourist2.id,
            homestay_id=h2.id,
            rating=5,
            review_text="Highly recommend the canoe ride! The host is so friendly and does amazing work to protect backwater wildlife.",
            sentiment_score=0.8,
            sentiment_label="positive"
        )
        
        # Homestay 3 Reviews
        r3_1 = Review(
            tourist_id=tourist1.id,
            homestay_id=h3.id,
            rating=4,
            review_text="A very cozy mud hut. Clean water was a bit limited but that is expected in the desert. Stargazing session was unforgettable.",
            sentiment_score=0.5,
            sentiment_label="positive"
        )
        
        db.session.add_all([r1_1, r1_2, r2_1, r2_2, r3_1])
        
        # 5. Add Bookings (Past & Future)
        # Tourist 1 booked Homestay 1 in the past
        b1 = Booking(
            tourist_id=tourist1.id,
            homestay_id=h1.id,
            check_in=date(2026, 5, 12),
            check_out=date(2026, 5, 15),
            total_guests=2,
            total_price=255.00,
            status="completed",
            created_at=datetime(2026, 5, 1)
        )
        
        # Tourist 2 has a pending booking for Homestay 2
        b2 = Booking(
            tourist_id=tourist2.id,
            homestay_id=h2.id,
            check_in=date(2026, 6, 20),
            check_out=date(2026, 6, 24),
            total_guests=1,
            total_price=280.00,
            status="pending",
            created_at=datetime(2026, 6, 5)
        )
        
        # Tourist 1 has a confirmed booking for Homestay 3
        b3 = Booking(
            tourist_id=tourist1.id,
            homestay_id=h3.id,
            check_in=date(2026, 7, 5),
            check_out=date(2026, 7, 8),
            total_guests=2,
            total_price=180.00,
            status="confirmed",
            created_at=datetime(2026, 6, 1)
        )
        
        # Add a bunch of simulated bookings for owner1 and owner2 to display historical trends in dashboard
        # Let's seed bookings for the past 6 months to generate nice stats
        today = date.today()
        for i in range(1, 40):
            # Pick a date in the past
            days_ago = i * 4
            booking_date = today - timedelta(days=days_ago)
            chk_in = booking_date
            chk_out = booking_date + timedelta(days=np.random.randint(2, 5))
            
            # Select homestay
            h_choice = h1 if i % 2 == 0 else h2 if i % 3 == 0 else h3
            
            # Guests
            guests = np.random.randint(1, 4)
            price = h_choice.price_per_night * guests * (chk_out - chk_in).days
            
            sim_booking = Booking(
                tourist_id=tourist2.id if i % 2 == 0 else tourist1.id,
                homestay_id=h_choice.id,
                check_in=chk_in,
                check_out=chk_out,
                total_guests=guests,
                total_price=price,
                status="completed",
                created_at=datetime.combine(chk_in - timedelta(days=np.random.randint(5, 15)), datetime.min.time())
            )
            db.session.add(sim_booking)

        db.session.add_all([b1, b2, b3])
        db.session.commit()
        
    print("Database seeded successfully with users, eco-homestays, activities, reviews, and bookings.")

if __name__ == "__main__":
    train_sentiment_model()
    train_demand_model()
    seed_database()
    print("All ML training and database initialization steps completed successfully.")
