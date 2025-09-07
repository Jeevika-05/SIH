import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, auth
import hashlib
import re
import time
import os
from dotenv import load_dotenv
import json

# Load .env
load_dotenv()

# Load Firebase creds from env
firebase_creds = os.getenv("FIREBASE_CREDS")

try:
    if not firebase_creds:
        raise ValueError("❌ FIREBASE_CREDS not found in .env")

    # Parse the JSON string
    cred_dict = json.loads(firebase_creds)

    # Fix private key newlines
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    st.success("🔥 Firebase Connected Successfully!")
    time.sleep(1)

except Exception as e:
    st.error(f"Firebase initialization error: {e}")
    db = None

# 🔹 Initialize session state
def initialize_session_state():
    defaults = {
        "current_screen": "splash",
        "language": "English",
        "mobile_number": "",
        "user_logged_in": False,
        "user_data": {},
        "login_attempts": 0,
        "registration_step": 1,
        "show_confetti": False,
        "firebase_uid": "",
        "verification_id": "",
        "otp_sent": False,
        "temp_mobile": "",
        "temp_password": ""
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# 🔹 Language translations
translations = {
    "English": {
        "app_name": "AgriSmart",
        "tagline": "Smart Agriculture Solutions for Modern Farmers",
        "select_language": "Select Your Language",
        "continue": "Continue",
        "get_started": "Get Started",
        "login": "Login",
        "signup": "Sign Up",
        "mobile_number": "Mobile Number",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "enter_mobile": "Enter your mobile number",
        "enter_password": "Enter your password",
        "create_password": "Create a secure password",
        "confirm_password_text": "Confirm your password",
        "login_button": "Login Now",
        "signup_button": "Create Account",
        "registration": "Complete Your Profile",
        "farmer_name": "Farmer Name",
        "land_size": "Land Size (acres)",
        "soil_type": "Soil Type",
        "previous_crop": "Previous Crop (Optional)",
        "complete_profile": "Complete Profile",
        "welcome": "🎉 Welcome to AgriSmart!",
        "welcome_back": "Welcome back",
        "season_detected": "Current Season",
        "invalid_mobile": "Please enter a valid 10-digit mobile number",
        "invalid_password": "Password must be at least 6 characters long",
        "passwords_dont_match": "Passwords don't match",
        "fill_required": "Please fill all required fields",
        "login_failed": "Invalid mobile number or password",
        "account_exists": "Account already exists. Please login instead.",
        "account_created": "🎊 Account Created Successfully!",
        "profile_updated": "✅ Profile Updated Successfully!",
        "logout": "Logout",
        "dashboard": "Dashboard",
        "my_profile": "My Profile",
        "max_attempts": "Too many failed attempts. Please try again later.",
        "creating_account": "Creating your account...",
        "logging_in": "Logging you in...",
        "updating_profile": "Updating your profile...",
        "success_message": "Congratulations! You're all set!",
    },
    "മലയാളം": {
        "app_name": "അഗ്രിസ്മാർട്ട്",
        "tagline": "ആധുനിക കർഷകർക്കുള്ള സ്മാർട്ട് കൃഷി പരിഹാരങ്ങൾ",
        "select_language": "നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക",
        "continue": "തുടരുക",
        "get_started": "ആരംഭിക്കുക",
        "login": "ലോഗിൻ",
        "signup": "സൈൻ അപ്പ്",
        "mobile_number": "മൊബൈൽ നമ്പർ",
        "password": "പാസ്‌വേഡ്",
        "confirm_password": "പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക",
        "enter_mobile": "മൊബൈൽ നമ്പർ നൽകുക",
        "enter_password": "പാസ്‌വേഡ് നൽകുക",
        "create_password": "സുരക്ഷിത പാസ്‌വേഡ് സൃഷ്ടിക്കുക",
        "confirm_password_text": "പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക",
        "login_button": "ഇപ്പോൾ ലോഗിൻ ചെയ്യുക",
        "signup_button": "അക്കൗണ്ട് സൃഷ്ടിക്കുക",
        "registration": "നിങ്ങളുടെ പ്രൊഫൈൽ പൂർത്തിയാക്കുക",
        "farmer_name": "കർഷകന്റെ പേര്",
        "land_size": "ഭൂമിയുടെ വലിപ്പം (എക്കറുകൾ)",
        "soil_type": "മണ്ണിന്റെ തരം",
        "previous_crop": "മുൻപത്തെ വിള (ഐച്ഛികം)",
        "complete_profile": "പ്രൊഫൈൽ പൂർത്തിയാക്കുക",
        "welcome": "🎉 അഗ്രിസ്മാർട്ടിലേക്ക് സ്വാഗതം!",
        "welcome_back": "തിരികെ സ്വാഗതം",
        "season_detected": "നിലവിലെ കാലാവസ്ഥ",
        "invalid_mobile": "സാധുവായ 10-അക്ക മൊബൈൽ നമ്പർ നൽകുക",
        "invalid_password": "പാസ്‌വേഡിൽ കുറഞ്ഞത് 6 അക്ഷരങ്ങൾ ഉണ്ടായിരിക്കണം",
        "passwords_dont_match": "പാസ്‌വേഡുകൾ പൊരുത്തപ്പെടുന്നില്ല",
        "fill_required": "എല്ലാ ആവശ്യമായ ഫീൽഡുകളും പൂരിപ്പിക്കുക",
        "login_failed": "തെറ്റായ മൊബൈൽ നമ്പർ അല്ലെങ്കിൽ പാസ്‌വേഡ്",
        "account_exists": "അക്കൗണ്ട് നിലവിലുണ്ട്. ലോഗിൻ ചെയ്യുക.",
        "account_created": "🎊 അക്കൗണ്ട് വിജയകരമായി സൃഷ്ടിച്ചു!",
        "profile_updated": "✅ പ്രൊഫൈൽ വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തു!",
        "logout": "ലോഗൗട്ട്",
        "dashboard": "ഡാഷ്ബോർഡ്",
        "my_profile": "എന്റെ പ്രൊഫൈൽ",
        "max_attempts": "വളരെയധികം തെറ്റായ ശ്രമങ്ങൾ. പിന്നീട് വീണ്ടും ശ്രമിക്കുക.",
        "creating_account": "അക്കൗണ്ട് സൃഷ്ടിക്കുന്നു...",
        "logging_in": "ലോഗിൻ ചെയ്യുന്നു...",
        "updating_profile": "പ്രൊഫൈൽ അപ്ഡേറ്റ് ചെയ്യുന്നു...",
        "success_message": "അഭിനന്ദനങ്ങൾ! എല്ലാം തയ്യാറാണ്!",
    },
}

def get_text(key):
    return translations[st.session_state.language].get(key, key)

# 🔹 Utility Functions
def detect_season():
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:
        return "Winter (Rabi Season) ❄️"
    elif current_month in [6, 7, 8, 9]:
        return "Monsoon (Kharif Season) 🌧️"
    else:
        return "Summer (Zaid Season) ☀️"

def validate_mobile(mobile):
    return re.match(r'^[6-9]\d{9}$', mobile) is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def show_loading_animation(message):
    """Display a loading animation with message"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        status_text.text(f"{message} {i + 1}%")
        time.sleep(0.02)
    
    status_text.text("✅ Complete!")
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()

def show_success_animation():
    """Show success animation with balloons and confetti"""
    st.balloons()
    time.sleep(1)
    
    # Custom confetti effect
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 4rem; animation: bounce 2s infinite;">🎉</div>
        <div style="font-size: 2rem; color: #28a745; margin: 1rem 0;">
            Success!
        </div>
    </div>
    <style>
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-30px);
        }
        60% {
            transform: translateY(-15px);
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 🔹 Firebase Authentication Functions
def create_firebase_user(mobile, password):
    """Create user in Firebase Authentication"""
    try:
        # In a real app, you'd use phone authentication
        # For demo purposes, we'll create with email format
        email = f"{mobile}@agrismart.com"
        
        user_record = auth.create_user(
            email=email,
            password=password,
            phone_number=f"+91{mobile}",
            display_name=f"Farmer {mobile}"
        )
        
        return user_record.uid
    except Exception as e:
        st.error(f"Firebase Auth error: {e}")
        return None

def authenticate_firebase_user(mobile, password):
    """Authenticate user using Firebase (simplified for demo)"""
    try:
        # In production, you'd verify the user properly
        # For demo, we'll check if user exists in Firestore
        doc_ref = db.collection("farmers").document(mobile)
        doc = doc_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            if user_data.get('password') == hash_password(password):
                return user_data
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

# 🔹 Database Functions
def check_user_exists(mobile):
    """Check if user exists in Firestore"""
    if db is None:
        return False
    
    try:
        doc_ref = db.collection("farmers").document(mobile)
        doc = doc_ref.get()
        return doc.exists
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def create_user_account(mobile, password):
    """Create user account in both Firebase Auth and Firestore"""
    if db is None:
        st.error("Database not available")
        return False
    
    try:
        # Create Firebase Auth user
        firebase_uid = create_firebase_user(mobile, password)
        
        if firebase_uid:
            # Store user data in Firestore
            user_data = {
                "mobile": mobile,
                "password": hash_password(password),
                "firebase_uid": firebase_uid,
                "created_at": datetime.now(),
                "profile_completed": False,
                "last_login": datetime.now()
            }
            
            db.collection("farmers").document(mobile).set(user_data)
            st.session_state.firebase_uid = firebase_uid
            return True
        return False
    except Exception as e:
        st.error(f"Account creation error: {e}")
        return False

def update_user_profile(mobile, profile_data):
    """Update user profile in Firestore"""
    if db is None:
        return False
    
    try:
        doc_ref = db.collection("farmers").document(mobile)
        profile_data.update({
            "profile_completed": True,
            "updated_at": datetime.now()
        })
        doc_ref.update(profile_data)
        return True
    except Exception as e:
        st.error(f"Profile update error: {e}")
        return False

# 🔹 Enhanced Splash Screen
def splash_screen():
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 2rem 0;">
        <div style="animation: fadeIn 2s;">
            <h1 style="color: white; font-size: 4rem; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🌾 AgriSmart
            </h1>
            <p style="font-size: 1.5rem; color: #f8f9fa; margin-bottom: 2rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                Smart Agriculture Solutions for Modern Farmers
            </p>
            <div style="font-size: 3rem; margin: 2rem 0; animation: bounce 2s infinite;">
                🚜🌱🌾
            </div>
        </div>
    </div>
    
    <style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-30px); }
        60% { transform: translateY(-15px); }
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🌍 " + get_text("select_language"))
        language = st.selectbox(
            "", 
            options=["English", "മലയാളം"], 
            index=0, 
            key="language_selector"
        )
        
        if st.button(get_text("get_started"), use_container_width=True, type="primary"):
            st.session_state.language = language
            with st.spinner("Loading AgriSmart..."):
                time.sleep(1.5)
            st.session_state.current_screen = "auth"
            st.rerun()

# 🔹 Enhanced Authentication Screen
def auth_screen():
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #2E7D32; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);">
            🌾 {get_text("app_name")}
        </h1>
        <p style="color: #666; font-size: 1.1rem;">{get_text("tagline")}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Animated tabs
        st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 10px 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        login_tab, signup_tab = st.tabs([
            f"🔑 {get_text('login')}", 
            f"🆕 {get_text('signup')}"
        ])
        
        with login_tab:
            enhanced_login_form()
        
        with signup_tab:
            enhanced_signup_form()

def enhanced_login_form():
    st.markdown("### 👋 " + get_text("welcome_back"))
    
    if st.session_state.login_attempts >= 5:
        st.error(get_text("max_attempts"))
        st.info("🕐 Please wait 5 minutes before trying again")
        return
    
    with st.form("login_form", clear_on_submit=True):
        mobile = st.text_input(
            "📱 " + get_text("mobile_number"), 
            placeholder=get_text("enter_mobile"),
            max_chars=10,
            help="Enter your 10-digit mobile number"
        )
        
        password = st.text_input(
            "🔒 " + get_text("password"), 
            type="password",
            placeholder=get_text("enter_password"),
            help="Enter your password"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            login_button = st.form_submit_button(
                get_text("login_button"), 
                use_container_width=True, 
                type="primary"
            )
        
        if login_button:
            if not validate_mobile(mobile):
                st.error("❌ " + get_text("invalid_mobile"))
                return
            
            if len(password) < 6:
                st.error("❌ " + get_text("invalid_password"))
                return
            
            # Show loading animation
            with st.spinner(get_text("logging_in")):
                time.sleep(1.5)  # Simulate processing time
                
                user_data = authenticate_firebase_user(mobile, password)
                
                if user_data:
                    st.success("✅ Login Successful!")
                    
                    # Update session state
                    st.session_state.user_logged_in = True
                    st.session_state.mobile_number = mobile
                    st.session_state.user_data = user_data
                    st.session_state.login_attempts = 0
                    st.session_state.firebase_uid = user_data.get('firebase_uid', '')
                    
                    # Update last login
                    if db:
                        db.collection("farmers").document(mobile).update({
                            "last_login": datetime.now()
                        })
                    
                    show_success_animation()
                    
                    # Navigate to appropriate screen
                    if user_data.get("profile_completed", False):
                        st.session_state.current_screen = "dashboard"
                    else:
                        st.session_state.current_screen = "registration"
                    
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error("❌ " + get_text("login_failed"))
                    
                    # Show remaining attempts
                    remaining = 5 - st.session_state.login_attempts
                    if remaining > 0:
                        st.warning(f"⚠️ {remaining} attempts remaining")

def enhanced_signup_form():
    st.markdown("### 🎯 " + get_text("signup"))
    
    with st.form("signup_form", clear_on_submit=True):
        mobile = st.text_input(
            "📱 " + get_text("mobile_number"), 
            placeholder=get_text("enter_mobile"),
            max_chars=10,
            help="This will be your username"
        )
        
        password = st.text_input(
            "🔒 " + get_text("password"), 
            type="password",
            placeholder=get_text("create_password"),
            help="At least 6 characters"
        )
        
        confirm_password = st.text_input(
            "🔐 " + get_text("confirm_password"), 
            type="password",
            placeholder=get_text("confirm_password_text")
        )
        
        # Password strength indicator
        if password:
            strength = calculate_password_strength(password)
            color = "#dc3545" if strength < 3 else "#ffc107" if strength < 5 else "#28a745"
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <small>Password Strength: </small>
                <div style="background: #e9ecef; height: 8px; border-radius: 4px;">
                    <div style="background: {color}; height: 8px; width: {strength * 20}%; border-radius: 4px; transition: width 0.3s;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        signup_button = st.form_submit_button(
            get_text("signup_button"), 
            use_container_width=True, 
            type="primary"
        )
        
        if signup_button:
            if not validate_mobile(mobile):
                st.error("❌ " + get_text("invalid_mobile"))
                return
            
            if len(password) < 6:
                st.error("❌ " + get_text("invalid_password"))
                return
            
            if password != confirm_password:
                st.error("❌ " + get_text("passwords_dont_match"))
                return
            
            if check_user_exists(mobile):
                st.error("❌ " + get_text("account_exists"))
                return
            
            # Show loading animation
            with st.spinner(get_text("creating_account")):
                show_loading_animation("Creating your account")
                
                if create_user_account(mobile, password):
                    st.success("🎉 " + get_text("account_created"))
                    
                    # Update session state
                    st.session_state.user_logged_in = True
                    st.session_state.mobile_number = mobile
                    st.session_state.temp_mobile = mobile
                    st.session_state.temp_password = password
                    
                    show_success_animation()
                    
                    st.info("👨‍🌾 Let's complete your farmer profile!")
                    time.sleep(2)
                    
                    st.session_state.current_screen = "registration"
                    st.rerun()

def calculate_password_strength(password):
    """Calculate password strength score (0-5)"""
    score = 0
    if len(password) >= 6: score += 1
    if len(password) >= 8: score += 1
    if re.search(r'[A-Z]', password): score += 1
    if re.search(r'[0-9]', password): score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 1
    return score

# 🔹 Enhanced Registration Screen
def registration_screen():
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #2E7D32;">🌾 {get_text("app_name")}</h1>
        <h3 style="color: #666;">👨‍🌾 {get_text("registration")}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    current_season = detect_season()
    st.info(f"🌱 **{get_text('season_detected')}:** {current_season}")
    
    # Progress indicator
    progress = st.progress(0.7, text="Profile completion: 70%")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            farmer_name = st.text_input(
                "👤 " + get_text("farmer_name"), 
                value=st.session_state.user_data.get("name", ""),
                help="Enter your full name"
            )
            
            land_size = st.number_input(
                "🚜 " + get_text("land_size"), 
                min_value=0.1, 
                max_value=1000.0, 
                step=0.1, 
                format="%.1f",
                value=st.session_state.user_data.get("land_size", 1.0),
                help="Total land area you cultivate"
            )
        
        with col2:
            soil_types = ["Clay", "Sandy", "Loamy", "Silt", "Peaty", "Chalky"]
            soil_type = st.selectbox(
                "🏔️ " + get_text("soil_type"), 
                soil_types,
                index=soil_types.index(st.session_state.user_data.get("soil_type", "Loamy")),
                help="Select your predominant soil type"
            )
            
            kerala_crops = [
                "Coconut", "Rubber", "Tea", "Coffee", "Arecanut",
                "Rice (Paddy)", "Banana", "Plantain", "Cassava (Tapioca)", 
                "Black Pepper", "Cardamom", "Clove", "Nutmeg",
                "Jackfruit", "Mango", "Pineapple", "Papaya",
                "Sugarcane", "Cocoa", "Cashew"
            ]
            
            previous_crop = st.selectbox(
                "🌾 " + get_text("previous_crop"), 
                ["None"] + sorted(kerala_crops),
                help="What did you grow last season?"
            )
        
        st.markdown("---")
        
        submit_button = st.form_submit_button(
            f"✅ {get_text('complete_profile')}", 
            use_container_width=True, 
            type="primary"
        )
        
        if submit_button:
            if farmer_name and land_size > 0:
                progress.progress(1.0, text="Profile completion: 100%")
                
                with st.spinner(get_text("updating_profile")):
                    show_loading_animation("Setting up your profile")
                    
                    profile_data = {
                        "name": farmer_name,
                        "land_size": land_size,
                        "soil_type": soil_type,
                        "previous_crop": previous_crop if previous_crop != "None" else None,
                        "season": current_season,
                        "registration_completed_at": datetime.now()
                    }
                    
                    if update_user_profile(st.session_state.mobile_number, profile_data):
                        st.success("🎊 " + get_text("profile_updated"))
                        st.session_state.user_data.update(profile_data)
                        
                        # Show celebration
                        show_success_animation()
                        
                        st.markdown(f"""
                        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #28a745, #20c997); border-radius: 15px; color: white; margin: 2rem 0;">
                            <h2>🎉 {get_text("success_message")}</h2>
                            <p>Welcome to the AgriSmart community, {farmer_name}!</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        time.sleep(3)
                        st.session_state.current_screen = "dashboard"
                        st.rerun()
            else:
                st.error("❌ " + get_text("fill_required"))

# 🔹 Enhanced Dashboard Screen
def dashboard_screen():
    # Header with logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <h1 style="color: #2E7D32; margin-bottom: 0;">
            🌾 {get_text('app_name')} - {get_text('dashboard')}
        </h1>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("🚪 " + get_text("logout"), type="secondary", use_container_width=True):
            logout()

    user_name = st.session_state.user_data.get("name", "Farmer")
    
    # Welcome message with animation
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
        <h2 style="color: white; margin-bottom: 1rem;">
            🌟 {get_text('welcome_back')}, {user_name}! 👋
        </h2>
        <p style="color: #f8f9fa; font-size: 1.1rem;">
            Ready to make your farming smarter today?
        </p>
    </div>
    """, unsafe_allow_html=True)

    current_season = detect_season()
    
    # Enhanced Dashboard cards with animations
    st.markdown("### 📊 Your Farm Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                    padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌱</div>
            <h4 style="margin: 0; color: white;">Current Season</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">{}</p>
            <small style="opacity: 0.8;">Active Now</small>
        </div>
        """.format(current_season), unsafe_allow_html=True)
    
    with col2:
        land_size = st.session_state.user_data.get('land_size', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fd7e14, #ffc107); 
                    padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚜</div>
            <h4 style="margin: 0; color: white;">Land Size</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">{land_size} acres</p>
            <small style="opacity: 0.8;">Registered</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        soil_type = st.session_state.user_data.get('soil_type', 'Unknown')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #6f42c1, #e83e8c); 
                    padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌾</div>
            <h4 style="margin: 0; color: white;">Soil Type</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">{soil_type}</p>
            <small style="opacity: 0.8;">Identified</small>
        </div>
        """, unsafe_allow_html=True)

    # Quick Actions Section
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🌡️\nWeather", use_container_width=True):
            st.info("🌤️ Weather feature coming soon!")
    
    with col2:
        if st.button("💧\nIrrigation", use_container_width=True):
            st.info("💦 Irrigation management coming soon!")
    
    with col3:
        if st.button("🌱\nCrop Guide", use_container_width=True):
            st.info("📚 Crop recommendations coming soon!")
    
    with col4:
        if st.button("📱\nSupport", use_container_width=True):
            st.info("🎧 24/7 Support: +91-1800-AGRI-HELP")

    # Profile section with enhanced styling
    st.markdown("### 👤 " + get_text("my_profile"))
    
    with st.expander("📋 View Profile Details", expanded=False):
        profile_data = {
            "👤 Name": st.session_state.user_data.get("name"),
            "📱 Mobile": st.session_state.mobile_number,
            "🚜 Land Size": f"{st.session_state.user_data.get('land_size')} acres",
            "🌾 Soil Type": st.session_state.user_data.get('soil_type'),
            "🌱 Previous Crop": st.session_state.user_data.get('previous_crop', 'None'),
            "🗓️ Current Season": current_season,
            "📅 Member Since": st.session_state.user_data.get('created_at', 'N/A')
        }
        
        for key, value in profile_data.items():
            st.markdown(f"**{key}:** {value}")
    
    # Recent Activity Section
    st.markdown("### 📈 Recent Activity")
    
    # Sample activity data
    activities = [
        {"icon": "🌱", "action": "Profile completed", "time": "Today", "status": "success"},
        {"icon": "🔐", "action": "Account created", "time": "Today", "status": "success"},
        {"icon": "👋", "action": "Welcome to AgriSmart!", "time": "Today", "status": "info"}
    ]
    
    for activity in activities:
        status_color = {
            "success": "#28a745",
            "info": "#17a2b8",
            "warning": "#ffc107"
        }.get(activity["status"], "#6c757d")
        
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                    margin: 0.5rem 0; border-left: 4px solid {status_color};">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 1rem;">{activity["icon"]}</span>
                <div>
                    <strong>{activity["action"]}</strong>
                    <br><small style="color: #6c757d;">{activity["time"]}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 2rem 0;">
        <p>🌾 <strong>AgriSmart</strong> - Empowering Farmers with Technology</p>
        <p><small>Made with ❤️ for Indian Farmers | Version 2.0</small></p>
    </div>
    """, unsafe_allow_html=True)

def logout():
    """Enhanced logout with confirmation"""
    if st.session_state.get('user_logged_in', False):
        # Show logout animation
        st.info("👋 Logging out...")
        with st.spinner("Saving your session..."):
            time.sleep(1)
        
        # Clear user session
        keys_to_clear = [
            "user_logged_in", "mobile_number", "user_data", 
            "firebase_uid", "registration_step", "temp_mobile", "temp_password"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.current_screen = "splash"
        st.success("✅ Logged out successfully!")
        time.sleep(1)
        st.rerun()

# 🔹 Main App with Enhanced Styling
def main():
    st.set_page_config(
        page_title="AgriSmart - Smart Agriculture App", 
        page_icon="🌾", 
        layout="centered", 
        initial_sidebar_state="collapsed"
    )

    # Enhanced CSS styling
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Button Enhancements */
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
    
    /* Form Enhancements */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        padding: 0.75rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e9ecef;
    }
    
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e9ecef;
    }
    
    /* Tab Enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.1);
        padding: 4px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Success/Error Message Enhancements */
    .stSuccess {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
    }
    
    .stError {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.2);
    }
    
    .stInfo {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(23, 162, 184, 0.2);
    }
    
    /* Progress Bar Enhancement */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #28a745, #20c997);
        border-radius: 10px;
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Animation Classes */
    .fade-in {
        animation: fadeIn 1s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .bounce {
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-30px); }
        60% { transform: translateY(-15px); }
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .stApp {
            padding: 1rem;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        .stButton > button {
            padding: 0.5rem 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    initialize_session_state()

    # Route to appropriate screen with transition effects
    if st.session_state.current_screen == "splash":
        splash_screen()
    elif st.session_state.current_screen == "auth":
        auth_screen()
    elif st.session_state.current_screen == "registration":
        if st.session_state.user_logged_in:
            registration_screen()
        else:
            st.session_state.current_screen = "auth"
            st.rerun()
    elif st.session_state.current_screen == "dashboard":
        if st.session_state.user_logged_in:
            dashboard_screen()
        else:
            st.session_state.current_screen = "auth"
            st.rerun()

    # Enhanced Debug Panel
    if st.checkbox("🐛 Developer Mode", help="Show debug information"):
        with st.sidebar:
            st.markdown("### 🔍 Debug Information")
            
            debug_info = {
                "Current Screen": st.session_state.current_screen,
                "Language": st.session_state.language,
                "User Logged In": st.session_state.user_logged_in,
                "Mobile Number": st.session_state.mobile_number,
                "Firebase UID": st.session_state.get('firebase_uid', 'None'),
                "Database Status": "✅ Connected" if db else "❌ Disconnected",
                "Session Keys": len(st.session_state.keys())
            }
            
            for key, value in debug_info.items():
                st.text(f"{key}: {value}")
            
            st.markdown("---")
            
            if st.button("🔄 Reset Application", type="secondary", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("✅ Application reset!")
                time.sleep(1)
                st.rerun()
            
            if st.button("💾 Download Session Data", use_container_width=True):
                session_data = dict(st.session_state)
                # Convert datetime objects to strings for JSON serialization
                for key, value in session_data.items():
                    if isinstance(value, datetime):
                        session_data[key] = str(value)
                
                st.download_button(
                    "📄 Download JSON",
                    data=json.dumps(session_data, indent=2),
                    file_name="agrismart_session.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()