# EcoStay - AI-Powered Homestay & Eco-Tourism Platform

EcoStay is a full-stack platform designed to help rural and eco-friendly homestay owners establish an online presence, streamline their booking workflows, and connect with travelers. The platform incorporates machine learning models to provide personalized recommendations, review sentiment analysis, demand forecasting, and chatbot guidance.

## Key Features

### For Tourists
* **Discover Stays:** Search and filter homestays by location, price, rating, and specific eco-features (e.g., Solar Power, Organic Gardening, Rainwater Harvesting).
* **Booking System:** Interactive booking calendar and price calculator based on check-in/check-out dates and guest count.
* **AI Recommendation Engine:** Enter personalized travel preferences in plain text (e.g. *"quiet cottage near the mountains with home-cooked organic meals"*) and receive custom matched homestays with percentage scores.
* **Feedback & Reviews:** Leave star ratings and reviews, with AI auto-analyzing and labeling review sentiments.

### For Homestay Owners (Hosts)
* **Listing Management:** Create and manage homestay profile details, pricing, amenities, and eco-initiatives.
* **Activity Listings:** List host-led interactive workshops (e.g., trekking, organic farming, traditional cooking).
* **Booking Approval Queue:** Review, approve, or decline reservation requests from tourists.
* **AI Analytics Dashboard:** 
  * View monthly revenue trends via an interactive visual line graph.
  * Monitor visitor sentiment distribution (Positive, Neutral, Negative feedback ratios).
  * **AI Demand Forecasting Widget:** Predicts occupancy rates for the upcoming 6 months using local seasonal indicators, pricing structures, and rating feedback.

### AI Capabilities
1. **Chatbot Support:** TF-IDF intent-matching travel bot responding to questions about bookings, activities, and sustainable practices.
2. **Sentiment Analyzer:** Naive Bayes/Logistic Regression classifier evaluating text review sentiments.
3. **Demand Predictor:** Scikit-learn Ridge Regression predicting booking likelihood based on historical seasonality and listing details.
4. **Content-Based Recommender:** Cosine similarity comparison vectorizing text features against tourist inputs.

---

## Technology Stack
* **Backend:** Flask (Python), Flask-CORS, Flask-SQLAlchemy
* **Frontend:** Single Page Application (HTML5, CSS3, Modern ES6 JavaScript) featuring a premium glassmorphic dark theme and custom responsive SVG data charts.
* **Database:** SQLite (SQLAlchemy ORM - easily configurable for MySQL/PostgreSQL)
* **AI/ML:** Python, Scikit-learn, NumPy, Pandas

---

## Project Structure
```text
eco-homestay/
├── backend/
│   ├── app.py                # Flask main runner & API endpoints
│   ├── database.py           # SQLAlchemy database model classes
│   ├── ml_engine.py          # AI models (Recommender, Predictor, Sentiment, Chatbot)
│   ├── train_models.py       # ML training & DB seeding script
│   ├── requirements.txt      # Python dependencies
│   ├── static/               # Frontend resources
│   │   ├── css/style.css     # Premium dark theme stylesheet
│   │   └── js/app.js         # Core SPA client logic
│   └── templates/
│       └── index.html        # Front-end HTML template layout
├── .gitignore                # Git ignore patterns
└── README.md                 # Project documentation (this file)
```

---

## Getting Started

### 1. Set Up the Environment
Make sure Python 3.8+ is installed. Create a virtual environment and install dependencies:
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Train AI Models & Seed Database
Run the training script to generate the synthetic historical dataset, fit the ML classifiers, save model weights, and initialize the SQLite database:
```bash
python train_models.py
```

### 3. Run the Flask Server
Start the development server:
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser to explore and interact with the application!
