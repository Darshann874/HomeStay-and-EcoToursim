import os
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LinearRegression, LogisticRegression

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------
# 1. Recommendation Engine (Content-Based)
# -----------------
class RecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def recommend(self, user_preference_query, homestays):
        """
        user_preference_query: String of tourist's preferences, e.g. "solar power close to mountains trekking"
        homestays: List of Homestay database models or dict representations
        """
        if not homestays:
            return []
            
        # Extract features for each homestay
        homestay_docs = []
        for h in homestays:
            # Concatenate location, description, amenities, eco_features, and activities
            activities_str = " ".join([act.name + " " + act.description for act in h.activities]) if hasattr(h, 'activities') else ""
            doc = f"{h.name} {h.location} {h.description} {h.amenities} {h.eco_features} {activities_str}"
            homestay_docs.append(doc.lower())
            
        # Fit vectorizer on homestay profiles
        try:
            tfidf_matrix = self.vectorizer.fit_transform(homestay_docs)
            query_vector = self.vectorizer.transform([user_preference_query.lower()])
            
            # Calculate Cosine Similarities
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Pair each homestay with its score
            scored_homestays = []
            for idx, score in enumerate(similarities):
                scored_homestays.append((homestays[idx], float(score)))
                
            # Sort by score descending
            scored_homestays.sort(key=lambda x: x[1], reverse=True)
            return scored_homestays
        except Exception as e:
            print(f"Recommendation error: {e}")
            return [(h, 0.0) for h in homestays]

# -----------------
# 2. Sentiment Analyzer
# -----------------
class SentimentAnalyzer:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.load_model()
        
    def load_model(self):
        model_path = os.path.join(MODEL_DIR, 'sentiment_model.pkl')
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data['vectorizer']
                    self.model = data['model']
            except Exception as e:
                print(f"Error loading sentiment model: {e}")
                
    def analyze(self, text):
        """
        Analyzes review text and returns: (sentiment_score, sentiment_label)
        score is from -1.0 (negative) to 1.0 (positive)
        """
        if not text or len(text.strip()) == 0:
            return 0.0, 'neutral'
            
        # Fallback lexical check in case model is not trained/loaded
        if not self.model or not self.vectorizer:
            pos_words = {'beautiful', 'clean', 'wonderful', 'amazing', 'great', 'excellent', 'hospitable', 'friendly', 'love', 'perfect', 'eco', 'sustainable', 'nature'}
            neg_words = {'dirty', 'noisy', 'expensive', 'bad', 'rude', 'poor', 'unclean', 'disappointing', 'horrible', 'waste', 'broken', 'cold'}
            words = text.lower().split()
            pos_count = sum(1 for w in words if w in pos_words)
            neg_count = sum(1 for w in words if w in neg_words)
            
            diff = pos_count - neg_count
            total = pos_count + neg_count
            score = diff / max(total, 1)
            # Clip between -1 and 1
            score = max(-1.0, min(1.0, score * 0.5))
            
            if score > 0.15:
                label = 'positive'
            elif score < -0.15:
                label = 'negative'
            else:
                label = 'neutral'
            return float(score), label
            
        try:
            vec = self.vectorizer.transform([text])
            # Predict probabilities
            probs = self.model.predict_proba(vec)[0] # [neg_prob, neutral_prob, pos_prob]
            classes = self.model.classes_
            
            # Label
            label = self.model.predict(vec)[0]
            
            # Score estimation based on probability distributions
            neg_idx = np.where(classes == 'negative')[0][0]
            neutral_idx = np.where(classes == 'neutral')[0][0]
            pos_idx = np.where(classes == 'positive')[0][0]
            
            score = float(probs[pos_idx] - probs[neg_idx])
            return score, label
        except Exception as e:
            print(f"Inference error in sentiment analysis: {e}")
            return 0.0, 'neutral'

# -----------------
# 3. Booking Demand Predictor
# -----------------
class DemandPredictor:
    def __init__(self):
        self.model = None
        self.location_encoder = None
        self.load_model()
        
    def load_model(self):
        model_path = os.path.join(MODEL_DIR, 'demand_model.pkl')
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.location_encoder = data['location_encoder']
            except Exception as e:
                print(f"Error loading demand model: {e}")
                
    def predict_occupancy(self, month, location, price, rating):
        """
        Predicts the monthly occupancy rate (0-100%) for a homestay
        """
        # Fallback: simple trend calculation if model is not loaded
        if not self.model or not self.location_encoder:
            # Basic peak seasons: Summer (May-July: 5-7), Winter (Dec-Jan: 12-1)
            base_occupancy = 45.0
            
            # Seasonal factor
            if month in [5, 6, 7, 12]:
                base_occupancy += 25.0
            elif month in [4, 8, 10, 11]:
                base_occupancy += 10.0
            else:
                base_occupancy -= 15.0
                
            # Rating factor
            base_occupancy += (rating - 3.0) * 15.0
            
            # Price factor: higher price reduces occupancy
            if price > 150:
                base_occupancy -= 15.0
            elif price < 50:
                base_occupancy += 10.0
                
            # Random slight fluctuation
            np.random.seed(int(month + price))
            noise = np.random.normal(0, 3.0)
            
            return float(max(5.0, min(95.0, base_occupancy + noise)))
            
        try:
            # Encode location
            loc_code = self.location_encoder.get(location.lower(), 0)
            
            # Predict
            X = np.array([[month, loc_code, price, rating]])
            prediction = self.model.predict(X)[0]
            return float(max(0.0, min(100.0, prediction)))
        except Exception as e:
            print(f"Inference error in demand predictor: {e}")
            return 50.0

# -----------------
# 4. Travel Chatbot Helper
# -----------------
class TravelChatbot:
    def __init__(self):
        self.intents = [
            {
                "keywords": ["hello", "hi", "hey", "greetings"],
                "response": "Hello traveler! I am your Eco-Homestay Guide. Ask me about homestays, green living tips, local activities, or how to manage bookings!"
            },
            {
                "keywords": ["book", "booking", "reserve", "how to book"],
                "response": "To book a stay, click on any homestay card from our Explore page, choose your check-in/check-out dates, set the guest count, and click 'Book Now'. Homestay owners will approve or reject your booking directly."
            },
            {
                "keywords": ["eco", "sustainable", "green", "environment", "carbon"],
                "response": "Our platform promotes green stays! Look for the 'Eco-Features' badge on listings. Features like solar energy, organic farming, waste management, and local craft support ensure your stay empowers local ecosystems."
            },
            {
                "keywords": ["owner", "host", "list my", "dashboard"],
                "response": "If you are an owner, you can toggle to Host View (register as an owner first) and list your homestay, manage activities, approve bookings, and view visitor trend analysis and booking demand forecasts!"
            },
            {
                "keywords": ["food", "eat", "local cuisine", "meals"],
                "response": "Most rural homestays offer authentic, home-cooked organic meals using locally harvested ingredients. Be sure to check the description or ask your host for traditional cooking activities during your visit!"
            },
            {
                "keywords": ["activities", "trek", "hike", "crafts", "farming"],
                "response": "Local activities connect you directly with rural cultures. Owners list interactive experiences like guided hikes, organic farming sessions, traditional cooking lessons, or pottery weaving. You can view these under 'Local Activities' on details pages."
            }
        ]
        # Set up a TF-IDF system for matching complex queries
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.intent_docs = [" ".join(intent["keywords"]) for intent in self.intents]
        self.tfidf_matrix = self.vectorizer.fit_transform(self.intent_docs)

    def get_reply(self, message):
        if not message or len(message.strip()) == 0:
            return "I didn't catch that. Could you repeat?"
            
        # Match using TF-IDF cosine similarity
        try:
            query_vec = self.vectorizer.transform([message.lower()])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            best_idx = np.argmax(similarities)
            
            if similarities[best_idx] > 0.15:
                return self.intents[best_idx]["response"]
        except Exception:
            pass
            
        # Fallback Keyword check
        message_lower = message.lower()
        for intent in self.intents:
            for kw in intent["keywords"]:
                if kw in message_lower:
                    return intent["response"]
                    
        return "That's an interesting question! I am constantly learning about rural travel. You can ask me how to book a homestay, what eco-features mean, or how owners manage booking demand prediction."
