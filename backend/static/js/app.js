const app = {
    // Application State
    state: {
        user: null,
        activePage: 'explore',
        homestays: [],
        selectedHomestay: null,
        ratingValue: 0,
        apiBaseUrl: '/api' // Using relative API base since we are served from Flask
    },

    // Initialization
    init() {
        console.log("Initializing EcoStay application...");
        lucide.createIcons();
        this.checkSession();
        this.fetchHomestays();
        
        // Auto set default booking dates
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        document.getElementById('book-check-in').value = today.toISOString().split('T')[0];
        document.getElementById('book-check-out').value = tomorrow.toISOString().split('T')[0];
    },

    // Navigation and Routing
    navigateTo(pageId) {
        console.log(`Navigating to page: ${pageId}`);
        
        // Update active class on nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.getElementById(`nav-${pageId}`);
        if (activeLink) activeLink.classList.add('active');
        
        // Hide all pages, show selected page
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        const targetPage = document.getElementById(`page-${pageId}`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.state.activePage = pageId;
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // Load page-specific data
        if (pageId === 'tourist-db') {
            this.fetchTouristDashboard();
        } else if (pageId === 'owner-db') {
            this.fetchHostDashboard();
        } else if (pageId === 'explore') {
            this.fetchHomestays();
        }
    },

    // Authentication Actions
    async checkSession() {
        try {
            // Include user_id in Auth header as fallback for cookies
            const userId = localStorage.getItem('eco_user_id');
            const headers = {};
            if (userId) {
                headers['Authorization'] = `Bearer ${userId}`;
            }

            const response = await fetch(`${this.state.apiBaseUrl}/auth/me`, { headers });
            const data = await response.json();
            
            if (data.user) {
                this.setLoggedInUser(data.user);
            } else {
                this.setLoggedOut();
            }
        } catch (error) {
            console.error("Session verification error:", error);
            this.setLoggedOut();
        }
    },

    setLoggedInUser(user) {
        this.state.user = user;
        localStorage.setItem('eco_user_id', user.id);
        
        // Show/hide navigation based on login status and role
        document.getElementById('nav-auth').style.display = 'none';
        document.getElementById('nav-user-badge').style.display = 'block';
        document.getElementById('nav-user-name').innerText = user.name;
        
        if (user.role === 'owner') {
            document.getElementById('nav-owner-db').style.display = 'block';
            document.getElementById('nav-tourist-db').style.display = 'none';
            document.getElementById('booking-login-warning').style.display = 'none';
        } else {
            document.getElementById('nav-owner-db').style.display = 'none';
            document.getElementById('nav-tourist-db').style.display = 'block';
            document.getElementById('booking-login-warning').style.display = 'none';
        }
        
        lucide.createIcons();
    },

    setLoggedOut() {
        this.state.user = null;
        localStorage.removeItem('eco_user_id');
        document.getElementById('nav-auth').style.display = 'block';
        document.getElementById('nav-user-badge').style.display = 'none';
        document.getElementById('nav-owner-db').style.display = 'none';
        document.getElementById('nav-tourist-db').style.display = 'none';
        document.getElementById('booking-login-warning').style.display = 'block';
    },

    async handleAuthSubmit(event) {
        event.preventDefault();
        const alertBox = document.getElementById('auth-alert');
        alertBox.style.display = 'none';
        
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        const isSignUp = document.getElementById('auth-submit-btn').innerText === 'Sign Up';
        
        let url = `${this.state.apiBaseUrl}/auth/login`;
        let payload = { email, password };
        
        if (isSignUp) {
            url = `${this.state.apiBaseUrl}/auth/register`;
            const name = document.getElementById('auth-name').value;
            const role = document.querySelector('input[name="auth-role"]:checked').value;
            payload = { email, password, name, role };
        }
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Authentication failed.');
            }
            
            if (isSignUp) {
                // Automatically log in after registration
                const loginResponse = await fetch(`${this.state.apiBaseUrl}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const loginData = await loginResponse.json();
                this.setLoggedInUser(loginData.user);
            } else {
                this.setLoggedInUser(data.user);
            }
            
            // Clean inputs
            document.getElementById('auth-email').value = '';
            document.getElementById('auth-password').value = '';
            if (document.getElementById('auth-name')) document.getElementById('auth-name').value = '';
            
            // Navigate to explore
            this.navigateTo('explore');
        } catch (error) {
            alertBox.innerText = error.message;
            alertBox.className = 'alert-message error';
            alertBox.style.display = 'block';
        }
    },

    async logout() {
        try {
            await fetch(`${this.state.apiBaseUrl}/auth/logout`, { method: 'POST' });
        } catch (e) {
            console.error("Logout request failed:", e);
        }
        this.setLoggedOut();
        this.navigateTo('explore');
    },

    toggleAuthMode() {
        const title = document.getElementById('auth-title');
        const subtitle = document.getElementById('auth-subtitle');
        const submitBtn = document.getElementById('auth-submit-btn');
        const toggleText = document.getElementById('auth-toggle-text');
        const toggleLink = document.getElementById('auth-toggle-link');
        const signupFields = document.querySelectorAll('.signup-only');
        
        document.getElementById('auth-alert').style.display = 'none';
        
        if (submitBtn.innerText === 'Sign In') {
            title.innerText = 'Create Account';
            subtitle.innerText = 'Join our eco-tourism community';
            submitBtn.innerText = 'Sign Up';
            toggleText.innerText = 'Already have an account?';
            toggleLink.innerText = 'Sign In';
            signupFields.forEach(f => f.style.display = 'block');
        } else {
            title.innerText = 'Welcome Back';
            subtitle.innerText = 'Login to book rooms and see recommendations';
            submitBtn.innerText = 'Sign In';
            toggleText.innerText = "Don't have an account?";
            toggleLink.innerText = 'Sign Up';
            signupFields.forEach(f => f.style.display = 'none');
        }
        lucide.createIcons();
    },

    toggleRoleSelect(role) {
        document.querySelectorAll('.role-radio-label').forEach(label => {
            label.classList.remove('active');
        });
        document.getElementById(`label-role-${role}`).classList.add('active');
    },

    // Explore / Filtering
    async fetchHomestays() {
        const searchVal = document.getElementById('search-input').value;
        const locationVal = document.getElementById('filter-location').value;
        const priceVal = document.getElementById('filter-price').value;
        const ratingVal = document.getElementById('filter-rating').value;
        const ecoVal = document.getElementById('filter-eco').value;
        
        let url = `${this.state.apiBaseUrl}/homestays?max_price=${priceVal}`;
        if (searchVal) url += `&search=${encodeURIComponent(searchVal)}`;
        if (locationVal) url += `&location=${encodeURIComponent(locationVal)}`;
        if (ratingVal) url += `&min_rating=${ratingVal}`;
        if (ecoVal) url += `&eco_feature=${encodeURIComponent(ecoVal)}`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            this.state.homestays = data;
            this.renderHomestays(data);
        } catch (error) {
            console.error("Error fetching homestays:", error);
        }
    },

    async getAIRecommendations() {
        const prefVal = document.getElementById('ai-preference-input').value;
        if (!prefVal || prefVal.trim().length === 0) return;
        
        try {
            const response = await fetch(`${this.state.apiBaseUrl}/recommendations?preferences=${encodeURIComponent(prefVal)}`);
            const data = await response.json();
            this.state.homestays = data;
            this.renderHomestays(data, true);
        } catch (error) {
            console.error("AI recommendation error:", error);
        }
    },

    clearAIRecommendations() {
        document.getElementById('ai-preference-input').value = '';
        this.fetchHomestays();
    },

    renderHomestays(homestays, isAIRecommended = false) {
        const container = document.getElementById('homestays-container');
        container.innerHTML = '';
        
        if (homestays.length === 0) {
            container.innerHTML = '<div class="empty-state">No homestays found matching your criteria. Try adjusting the search filters.</div>';
            return;
        }
        
        homestays.forEach(h => {
            const primaryEcoFeature = h.eco_features && h.eco_features.length > 0 ? h.eco_features[0] : '';
            
            // Match badge if AI score is present
            const matchBadgeHTML = isAIRecommended && h.score !== undefined ? 
                `<div class="ai-match-badge">${Math.round(h.score * 100)}% Match</div>` : '';
                
            const card = document.createElement('div');
            card.className = 'homestay-card glass-panel glass-panel-hover';
            card.onclick = () => this.viewHomestayDetails(h.id);
            
            card.innerHTML = `
                <div class="card-img-wrapper">
                    <img class="card-img" src="${h.image_url || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80'}" alt="${h.name}">
                    <div class="eco-score-badge">
                        <i data-lucide="leaf" style="width:12px; height:12px;"></i> ${primaryEcoFeature || 'Sustainable'}
                    </div>
                    ${matchBadgeHTML}
                </div>
                <div class="card-content">
                    <span class="card-location">${h.location}</span>
                    <h3 class="card-title">${h.name}</h3>
                    <div class="card-rating">
                        <i data-lucide="star" class="star-icon" style="width:14px; height:14px;"></i>
                        <span style="font-weight:700;">${h.average_rating}</span>
                    </div>
                    <p class="card-desc">${h.description}</p>
                    <div class="card-badges">
                        ${(h.eco_features || []).slice(0, 3).map(e => `<span class="badge-tag badge-eco">${e}</span>`).join('')}
                        ${(h.amenities || []).slice(0, 2).map(a => `<span class="badge-tag">${a}</span>`).join('')}
                    </div>
                    <div class="card-footer">
                        <div class="card-price">$${h.price_per_night} <span>/ night</span></div>
                        <button class="btn btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Explore</button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
        
        lucide.createIcons();
    },

    // Homestay Details View
    async viewHomestayDetails(id) {
        try {
            const response = await fetch(`${this.state.apiBaseUrl}/homestays/${id}`);
            if (!response.ok) throw new Error("Could not load homestay details.");
            
            const h = await response.json();
            this.state.selectedHomestay = h;
            
            // Populate DOM
            document.getElementById('detail-image').src = h.image_url;
            document.getElementById('detail-title').innerText = h.name;
            document.getElementById('detail-location').querySelector('span').innerText = h.location;
            document.getElementById('detail-rating').innerText = h.average_rating;
            document.getElementById('detail-desc').innerText = h.description;
            document.getElementById('widget-price-num').innerText = h.price_per_night;
            
            // Eco Tags
            const ecoContainer = document.getElementById('detail-eco-tags');
            ecoContainer.innerHTML = h.eco_features.map(e => `<span class="badge-tag badge-eco">${e}</span>`).join('');
            
            // Activities
            const actContainer = document.getElementById('detail-activities');
            actContainer.innerHTML = '';
            if (!h.activities || h.activities.length === 0) {
                actContainer.innerHTML = '<div class="empty-state" style="padding: 1rem; width:100%; grid-column:span 2;">No custom activities listed yet.</div>';
            } else {
                h.activities.forEach(act => {
                    const actCard = document.createElement('div');
                    actCard.className = 'activity-card glass-panel';
                    actCard.innerHTML = `
                        <div class="activity-name">${act.name}</div>
                        <div class="activity-desc">${act.description}</div>
                        <div class="activity-price">$${act.price} <span>per person</span></div>
                    `;
                    actContainer.appendChild(actCard);
                });
            }
            
            // Review Sentiment Gauge calculations
            const reviews = h.reviews || [];
            let posCount = 0, neuCount = 0, negCount = 0;
            reviews.forEach(r => {
                if (r.sentiment_label === 'positive') posCount++;
                else if (r.sentiment_label === 'negative') negCount++;
                else neuCount++;
            });
            
            const totalReviews = reviews.length || 1;
            const posPct = Math.round((posCount / totalReviews) * 100);
            const neuPct = Math.round((neuCount / totalReviews) * 100);
            const negPct = Math.round((negCount / totalReviews) * 100);
            
            document.getElementById('feedback-avg-rating').innerText = h.average_rating;
            
            // Animate Bar gauges
            document.getElementById('gauge-pos-bar').style.width = `${posPct}%`;
            document.getElementById('gauge-pos-pct').innerText = `${posPct}%`;
            document.getElementById('gauge-neu-bar').style.width = `${neuPct}%`;
            document.getElementById('gauge-neu-pct').innerText = `${neuPct}%`;
            document.getElementById('gauge-neg-bar').style.width = `${negPct}%`;
            document.getElementById('gauge-neg-pct').innerText = `${negPct}%`;
            
            // Render Reviews list
            const reviewsList = document.getElementById('detail-reviews-list');
            reviewsList.innerHTML = '';
            if (reviews.length === 0) {
                reviewsList.innerHTML = '<div class="empty-state" style="padding: 2rem;">No reviews submitted yet. Be the first to leave a review!</div>';
            } else {
                reviews.forEach(r => {
                    const revBox = document.createElement('div');
                    revBox.className = 'review-item glass-panel';
                    revBox.style.marginBottom = '1rem';
                    revBox.innerHTML = `
                        <div class="review-meta">
                            <span class="review-author">${r.tourist_name}</span>
                            <div class="review-rating-sentiment">
                                <span>${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                                <span class="sentiment-tag ${r.sentiment_label}">${r.sentiment_label}</span>
                            </div>
                        </div>
                        <p class="review-text">${r.review_text}</p>
                    `;
                    reviewsList.appendChild(revBox);
                });
            }
            
            this.updateBookingPrice();
            this.navigateTo('details');
        } catch (e) {
            console.error(e);
            alert("Failed to load details: " + e.message);
        }
    },

    updateBookingPrice() {
        if (!this.state.selectedHomestay) return;
        
        const checkIn = new Date(document.getElementById('book-check-in').value);
        const checkOut = new Date(document.getElementById('book-check-out').value);
        const guests = parseInt(document.getElementById('book-guests').value) || 1;
        
        if (checkIn && checkOut && checkOut > checkIn) {
            const timeDiff = checkOut.getTime() - checkIn.getTime();
            const days = Math.ceil(timeDiff / (1000 * 3600 * 24));
            
            const total = this.state.selectedHomestay.price_per_night * days * guests;
            document.getElementById('widget-total-price').innerText = total.toFixed(2);
        } else {
            document.getElementById('widget-total-price').innerText = '0';
        }
    },

    async requestBooking() {
        if (!this.state.user) {
            alert("Please log in as a tourist to request a booking.");
            this.navigateTo('auth');
            return;
        }
        
        if (this.state.user.role !== 'tourist') {
            alert("Only registered tourists can book homestays.");
            return;
        }
        
        const checkInVal = document.getElementById('book-check-in').value;
        const checkOutVal = document.getElementById('book-check-out').value;
        const guestsVal = document.getElementById('book-guests').value;
        
        const payload = {
            tourist_id: this.state.user.id,
            homestay_id: this.state.selectedHomestay.id,
            check_in: checkInVal,
            check_out: checkOutVal,
            total_guests: parseInt(guestsVal)
        };
        
        try {
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = `Bearer ${this.state.user.id}`;

            const response = await fetch(`${this.state.apiBaseUrl}/bookings`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to request booking.');
            
            alert("Booking requested successfully! The host will review your request.");
            this.navigateTo('tourist-db');
        } catch (e) {
            alert(e.message);
        }
    },

    // Tourist Dashboard
    async fetchTouristDashboard() {
        try {
            const headers = {};
            if (this.state.user) {
                headers['Authorization'] = `Bearer ${this.state.user.id}`;
            }

            const response = await fetch(`${this.state.apiBaseUrl}/bookings?user_id=${this.state.user.id}`, { headers });
            const data = await response.json();
            
            // Stats counts
            let staysCount = 0, upcomingCount = 0, completedCount = 0;
            const listContainer = document.getElementById('tourist-bookings-list');
            listContainer.innerHTML = '';
            
            if (data.length === 0) {
                listContainer.innerHTML = '<div class="empty-state">You have no booking requests yet. Explore homestays to make a reservation!</div>';
            } else {
                data.forEach(b => {
                    staysCount++;
                    if (b.status === 'confirmed') upcomingCount++;
                    else if (b.status === 'completed') completedCount++;
                    
                    const item = document.createElement('div');
                    item.className = 'booking-item-card glass-panel';
                    
                    // Show Review button for completed bookings
                    const actionBtnHTML = b.status === 'completed' ? 
                        `<button class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="app.showAddReviewModal(${b.homestay_id})">Leave Review</button>` : '';
                        
                    item.innerHTML = `
                        <div class="booking-main">
                            <div class="booking-homestay-name">${b.homestay_name}</div>
                            <div class="booking-dates-guests">
                                <i data-lucide="map-pin" style="width:12px; height:12px; vertical-align:middle;"></i> ${b.homestay_location} &nbsp;|&nbsp;
                                <i data-lucide="calendar" style="width:12px; height:12px; vertical-align:middle;"></i> ${b.check_in} to ${b.check_out} &nbsp;|&nbsp;
                                <i data-lucide="users" style="width:12px; height:12px; vertical-align:middle;"></i> ${b.total_guests} Guest(s)
                            </div>
                        </div>
                        <div class="booking-price-status">
                            <span class="booking-total-price">$${b.total_price.toFixed(2)}</span>
                            <span class="status-badge ${b.status}">${b.status}</span>
                            ${actionBtnHTML}
                        </div>
                    `;
                    listContainer.appendChild(item);
                });
            }
            
            document.getElementById('tourist-stat-stays').innerText = staysCount;
            document.getElementById('tourist-stat-upcoming').innerText = upcomingCount;
            document.getElementById('tourist-stat-completed').innerText = completedCount;
            
            lucide.createIcons();
        } catch (e) {
            console.error(e);
        }
    },

    showAddReviewModal(homestayId) {
        document.getElementById('review-homestay-id').value = homestayId;
        document.getElementById('new-review-text').value = '';
        this.setRatingValue(0);
        
        document.getElementById('modal-add-review').classList.add('active');
    },

    setRatingValue(val) {
        this.state.ratingValue = val;
        document.getElementById('new-review-rating').value = val;
        
        const stars = document.getElementById('star-rating-buttons').children;
        for (let i = 0; i < stars.length; i++) {
            if (i < val) {
                stars[i].classList.add('active');
            } else {
                stars[i].classList.remove('active');
            }
        }
    },

    async submitReview(event) {
        event.preventDefault();
        const alertBox = document.getElementById('modal-alert-review');
        alertBox.style.display = 'none';
        
        const homestayId = document.getElementById('review-homestay-id').value;
        const rating = this.state.ratingValue;
        const comment = document.getElementById('new-review-text').value;
        
        if (rating === 0) {
            alertBox.innerText = "Please select a star rating.";
            alertBox.className = "alert-message error";
            alertBox.style.display = "block";
            return;
        }
        
        const payload = {
            tourist_id: this.state.user.id,
            homestay_id: parseInt(homestayId),
            rating: rating,
            review_text: comment
        };
        
        try {
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = `Bearer ${this.state.user.id}`;

            const response = await fetch(`${this.state.apiBaseUrl}/reviews`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to submit review.');
            
            alert(`Review submitted! AI Sentiment analysis label: ${data.review.sentiment_label}`);
            this.closeModal('add-review');
            this.fetchTouristDashboard();
        } catch (e) {
            alertBox.innerText = e.message;
            alertBox.className = "alert-message error";
            alertBox.style.display = "block";
        }
    },

    // Host Dashboard
    async fetchHostDashboard() {
        try {
            const headers = {};
            if (this.state.user) {
                headers['Authorization'] = `Bearer ${this.state.user.id}`;
            }

            const response = await fetch(`${this.state.apiBaseUrl}/owner/analytics?owner_id=${this.state.user.id}`, { headers });
            const data = await response.json();
            
            // Populate Host stats
            document.getElementById('owner-stat-bookings').innerText = data.total_bookings;
            document.getElementById('owner-stat-revenue').innerText = `$${data.total_revenue.toLocaleString()}`;
            
            // AI Reviews Sentiment
            const sentimentContainer = document.getElementById('owner-reviews-sentiment');
            const reviewsData = data.sentiment_breakdown || { positive: 0, neutral: 0, negative: 0 };
            const totalRev = reviewsData.positive + reviewsData.neutral + reviewsData.negative || 1;
            
            const posPct = Math.round((reviewsData.positive / totalRev) * 100);
            const neuPct = Math.round((reviewsData.neutral / totalRev) * 100);
            const negPct = Math.round((reviewsData.negative / totalRev) * 100);
            
            sentimentContainer.innerHTML = `
                <div class="sentiment-bar-row">
                    <span class="sentiment-bar-label">Positive (${reviewsData.positive})</span>
                    <div class="sentiment-bar-outer">
                        <div class="sentiment-bar-inner pos" style="width: ${posPct}%;"></div>
                    </div>
                    <span class="sentiment-percentage">${posPct}%</span>
                </div>
                <div class="sentiment-bar-row">
                    <span class="sentiment-bar-label">Neutral (${reviewsData.neutral})</span>
                    <div class="sentiment-bar-outer">
                        <div class="sentiment-bar-inner neu" style="width: ${neuPct}%;"></div>
                    </div>
                    <span class="sentiment-percentage">${neuPct}%</span>
                </div>
                <div class="sentiment-bar-row">
                    <span class="sentiment-bar-label">Negative (${reviewsData.negative})</span>
                    <div class="sentiment-bar-outer">
                        <div class="sentiment-bar-inner neg" style="width: ${negPct}%;"></div>
                    </div>
                    <span class="sentiment-percentage">${negPct}%</span>
                </div>
            `;
            
            // Fetch raw bookings list
            const bResponse = await fetch(`${this.state.apiBaseUrl}/bookings?user_id=${this.state.user.id}`, { headers });
            const bData = await bResponse.json();
            
            // Split into pending list and host listings list
            const pendingList = document.getElementById('owner-pending-bookings');
            pendingList.innerHTML = '';
            
            const pendingBookings = bData.filter(b => b.status === 'pending');
            if (pendingBookings.length === 0) {
                pendingList.innerHTML = '<div class="empty-state" style="padding:1.5rem;">No pending requests.</div>';
            } else {
                pendingBookings.forEach(b => {
                    const row = document.createElement('div');
                    row.className = 'booking-item-card glass-panel';
                    row.innerHTML = `
                        <div class="booking-main">
                            <div class="booking-homestay-name">${b.homestay_name}</div>
                            <div class="booking-dates-guests">
                                Tourist: <strong>${b.tourist_name}</strong> &nbsp;|&nbsp;
                                Dates: ${b.check_in} to ${b.check_out} &nbsp;|&nbsp;
                                Guests: ${b.total_guests}
                            </div>
                        </div>
                        <div class="booking-price-status" style="align-items:flex-end;">
                            <span class="booking-total-price">$${b.total_price.toFixed(2)}</span>
                            <div style="display:flex; gap:0.5rem; margin-top:0.4rem;">
                                <button class="btn btn-primary" style="padding:0.3rem 0.6rem; font-size:0.75rem;" onclick="app.updateBookingStatus(${b.id}, 'confirmed')">Approve</button>
                                <button class="btn btn-danger" style="padding:0.3rem 0.6rem; font-size:0.75rem;" onclick="app.updateBookingStatus(${b.id}, 'cancelled')">Decline</button>
                            </div>
                        </div>
                    `;
                    pendingList.appendChild(row);
                });
            }
            
            // Host listed homestays
            const hResponse = await fetch(`${this.state.apiBaseUrl}/homestays`);
            const hData = await hResponse.json();
            const ownedStays = hData.filter(h => h.owner_id === this.state.user.id);
            
            const staysList = document.getElementById('owner-homestays-list');
            staysList.innerHTML = '';
            
            if (ownedStays.length === 0) {
                staysList.innerHTML = '<div class="empty-state" style="padding:1.5rem;">You have not listed any homestays yet.</div>';
            } else {
                ownedStays.forEach(h => {
                    const row = document.createElement('div');
                    row.className = 'booking-item-card glass-panel';
                    row.innerHTML = `
                        <div class="booking-main">
                            <div class="booking-homestay-name" style="color:var(--primary);">${h.name}</div>
                            <div class="booking-dates-guests">
                                Rating: ${h.average_rating} ★ &nbsp;|&nbsp; Location: ${h.location} &nbsp;|&nbsp; Price: $${h.price_per_night}
                            </div>
                        </div>
                        <button class="btn btn-secondary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="app.showAddActivityModal(${h.id})">
                            <i data-lucide="plus" style="width:12px; height:12px; display:inline-block; vertical-align:middle;"></i> Activity
                        </button>
                    `;
                    staysList.appendChild(row);
                });
            }
            
            // Draw Demand prediction widget columns
            const predContainer = document.getElementById('owner-demand-predictions');
            predContainer.innerHTML = '';
            
            const predictionMap = data.demand_predictions || {};
            const keys = Object.keys(predictionMap);
            if (keys.length === 0) {
                predContainer.innerHTML = '<div class="empty-state" style="width:100%; padding: 1.5rem;">No forecasting data available. Create a listing first!</div>';
            } else {
                // Focus on the first listing's forecasts for display
                const selectedListingName = keys[0];
                const forecasts = predictionMap[selectedListingName];
                
                const titleLabel = document.createElement('div');
                titleLabel.style.width = '100%';
                titleLabel.style.fontSize = '0.9rem';
                titleLabel.style.fontWeight = '700';
                titleLabel.style.color = 'var(--text-main)';
                titleLabel.style.marginBottom = '0.75rem';
                titleLabel.innerText = `Forecast for ${selectedListingName}:`;
                predContainer.appendChild(titleLabel);
                
                const columnsFlex = document.createElement('div');
                columnsFlex.style.display = 'flex';
                columnsFlex.style.width = '100%';
                columnsFlex.style.gap = '1rem';
                
                forecasts.forEach(f => {
                    const col = document.createElement('div');
                    col.className = 'prediction-col';
                    col.innerHTML = `
                        <div class="prediction-month">${f.month}</div>
                        <div class="prediction-percentage">${f.occupancy}%</div>
                        <div class="prediction-bar-outer">
                            <div class="prediction-bar-inner" style="width: ${f.occupancy}%;"></div>
                        </div>
                    `;
                    columnsFlex.appendChild(col);
                });
                predContainer.appendChild(columnsFlex);
            }
            
            // Draw Dynamic SVG Revenue line chart
            this.drawRevenueChart(data.monthly_revenue || []);
            
            lucide.createIcons();
        } catch (e) {
            console.error("Dashboard error:", e);
        }
    },

    drawRevenueChart(monthlyRevenue) {
        const container = document.getElementById('revenue-chart-container');
        container.innerHTML = '';
        
        if (monthlyRevenue.length === 0) {
            container.innerHTML = '<div class="empty-state">No revenue milestones recorded yet.</div>';
            return;
        }
        
        // Setup SVG Dimensions
        const width = container.clientWidth || 350;
        const height = 220;
        const padding = 35;
        
        // Find min/max values
        const revenues = monthlyRevenue.map(m => m.revenue);
        const maxRev = Math.max(...revenues, 100);
        
        // Map points to SVG coordinates
        const points = [];
        const xStep = (width - padding * 2) / Math.max(monthlyRevenue.length - 1, 1);
        
        monthlyRevenue.forEach((m, idx) => {
            const x = padding + idx * xStep;
            const y = height - padding - ((m.revenue / maxRev) * (height - padding * 2));
            points.push({ x, y, month: m.month, revenue: m.revenue });
        });
        
        // Construct SVG string
        let svgHTML = `
            <svg class="chart-svg" viewBox="0 0 ${width} ${height}">
                <defs>
                    <linearGradient id="chart-gradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.35"/>
                        <stop offset="100%" stop-color="var(--primary)" stop-opacity="0.0"/>
                    </linearGradient>
                </defs>
                
                <!-- Grid Lines -->
                <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" class="chart-axis" />
                <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" class="chart-axis" />
        `;
        
        // Horizontal Y guide lines
        const guides = 3;
        for (let i = 1; i <= guides; i++) {
            const y = padding + (i * (height - padding * 2) / (guides + 1));
            const val = Math.round(maxRev - (i * maxRev / (guides + 1)));
            svgHTML += `
                <line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" class="chart-grid-line" />
                <text x="${padding - 5}" y="${y + 3}" class="chart-text" text-anchor="end">$${val}</text>
            `;
        }
        
        // X Axis labels
        points.forEach((p, idx) => {
            // Simplify month label E.g. "2026-05" -> "May"
            const dateObj = new Date(p.month + "-01");
            const labelStr = dateObj.toLocaleString('default', { month: 'short' });
            
            svgHTML += `
                <text x="${p.x}" y="${height - 10}" class="chart-text" text-anchor="middle">${labelStr}</text>
            `;
        });
        
        // Draw Line and Gradient Fill Area
        if (points.length > 0) {
            let linePath = `M ${points[0].x} ${points[0].y}`;
            let areaPath = `M ${points[0].x} ${height - padding} L ${points[0].x} ${points[0].y}`;
            
            for (let i = 1; i < points.length; i++) {
                linePath += ` L ${points[i].x} ${points[i].y}`;
                areaPath += ` L ${points[i].x} ${points[i].y}`;
            }
            
            areaPath += ` L ${points[points.length - 1].x} ${height - padding} Z`;
            
            svgHTML += `
                <path d="${areaPath}" class="chart-area" />
                <path d="${linePath}" class="chart-line" />
            `;
        }
        
        // Draw Milestones nodes (circles)
        points.forEach(p => {
            svgHTML += `
                <circle cx="${p.x}" cy="${p.y}" r="4.5" class="chart-point" />
                <text x="${p.x}" y="${p.y - 10}" class="chart-text" text-anchor="middle" font-weight="700" fill="var(--primary)">$${Math.round(p.revenue)}</text>
            `;
        });
        
        svgHTML += `</svg>`;
        container.innerHTML = svgHTML;
    },

    async updateBookingStatus(bookingId, status) {
        try {
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = `Bearer ${this.state.user.id}`;

            const response = await fetch(`${this.state.apiBaseUrl}/bookings/${bookingId}/status`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ status })
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to update booking status.');
            
            alert(`Booking has been ${status}!`);
            this.fetchHostDashboard();
        } catch (e) {
            alert(e.message);
        }
    },

    showAddHomestayModal() {
        document.getElementById('modal-alert-homestay').style.display = 'none';
        document.getElementById('new-h-name').value = '';
        document.getElementById('new-h-desc').value = '';
        document.getElementById('new-h-price').value = '';
        document.getElementById('new-h-amenities').value = '';
        document.getElementById('new-h-eco').value = '';
        document.getElementById('new-h-image').value = '';
        
        document.getElementById('modal-add-homestay').classList.add('active');
    },

    async submitNewHomestay(event) {
        event.preventDefault();
        const alertBox = document.getElementById('modal-alert-homestay');
        alertBox.style.display = 'none';
        
        const payload = {
            owner_id: this.state.user.id,
            name: document.getElementById('new-h-name').value,
            location: document.getElementById('new-h-location').value,
            description: document.getElementById('new-h-desc').value,
            price_per_night: parseFloat(document.getElementById('new-h-price').value),
            amenities: document.getElementById('new-h-amenities').value,
            eco_features: document.getElementById('new-h-eco').value,
            image_url: document.getElementById('new-h-image').value
        };
        
        try {
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = `Bearer ${this.state.user.id}`;

            const response = await fetch(`${this.state.apiBaseUrl}/homestays`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to create listing.');
            
            alert("Homestay listed successfully! Make sure to run the ML model to see forecasts.");
            this.closeModal('add-homestay');
            this.fetchHostDashboard();
        } catch (e) {
            alertBox.innerText = e.message;
            alertBox.className = "alert-message error";
            alertBox.style.display = "block";
        }
    },

    showAddActivityModal(homestayId) {
        document.getElementById('modal-alert-activity').style.display = 'none';
        document.getElementById('activity-homestay-id').value = homestayId;
        document.getElementById('new-act-name').value = '';
        document.getElementById('new-act-price').value = '';
        document.getElementById('new-act-desc').value = '';
        
        document.getElementById('modal-add-activity').classList.add('active');
    },

    async submitNewActivity(event) {
        event.preventDefault();
        const alertBox = document.getElementById('modal-alert-activity');
        alertBox.style.display = 'none';
        
        const homestayId = document.getElementById('activity-homestay-id').value;
        const payload = {
            name: document.getElementById('new-act-name').value,
            type: document.getElementById('new-act-type').value,
            price: parseFloat(document.getElementById('new-act-price').value) || 0.0,
            description: document.getElementById('new-act-desc').value
        };
        
        try {
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = `Bearer ${this.state.user.id}`;

            const response = await fetch(`${this.state.apiBaseUrl}/homestays/${homestayId}/activities`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to add activity.');
            
            alert("Local activity added to listing!");
            this.closeModal('add-activity');
            this.fetchHostDashboard();
        } catch (e) {
            alertBox.innerText = e.message;
            alertBox.className = "alert-message error";
            alertBox.style.display = "block";
        }
    },

    closeModal(modalId) {
        document.getElementById(`modal-${modalId}`).classList.remove('active');
    },

    // Chatbot support drawer
    toggleChatbot() {
        document.getElementById('chatbot-drawer').classList.toggle('active');
    },

    async sendChatMessage() {
        const input = document.getElementById('chatbot-text-input');
        const text = input.value.trim();
        if (!text) return;
        
        // Append user bubble
        this.appendChatBubble(text, 'user');
        input.value = '';
        
        try {
            const response = await fetch(`${this.state.apiBaseUrl}/chatbot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            
            // Append bot bubble
            this.appendChatBubble(data.reply, 'bot');
        } catch (error) {
            console.error("Chat error:", error);
            this.appendChatBubble("Sorry, I'm having trouble connecting to the network right now.", 'bot');
        }
    },

    appendChatBubble(text, sender) {
        const chatArea = document.getElementById('chatbot-messages');
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;
        bubble.innerText = text;
        
        chatArea.appendChild(bubble);
        chatArea.scrollTop = chatArea.scrollHeight;
    }
};

// Start application when DOM is fully loaded
window.addEventListener('DOMContentLoaded', () => app.init());
