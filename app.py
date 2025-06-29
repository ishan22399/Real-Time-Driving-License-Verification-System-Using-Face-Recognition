import os
import multiprocessing
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
import cv2
import sqlite3
import numpy as np
import face_recognition
from functools import partial, wraps
import time
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import db
from werkzeug.security import generate_password_hash
from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from pytz import timezone
import pytz
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env file
load_dotenv()

UPLOAD_FOLDER = 'uploads/driver_images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}  # Add your allowed extensions

# Create upload directories if they don't exist
os.makedirs('uploads/driver_images', exist_ok=True)
os.makedirs('uploads/license_images', exist_ok=True)
os.makedirs('uploads/holder_images', exist_ok=True)

cred = credentials.Certificate("license-verification-ab3ef-firebase-adminsdk-3h1lk-9923b5ceaa.json") # Firebase Admin SDK JSON File
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL', 'https://license-verification-ab3ef-default-rtdb.firebaseio.com/') # Firebase Database URL
})
firebase_db = db.reference()


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'stark')  # Use environment variable or default
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['LICENSE_IMAGE_UPLOAD_FOLDER'] = 'uploads/license_images'
app.config['HOLDER_IMAGE_UPLOAD_FOLDER'] = 'uploads/holder_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Add custom Jinja2 filters
@app.template_filter('datetime_format')
def datetime_format(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime value or return current datetime formatted."""
    if value == "now" or value is None:
        return datetime.now().strftime(format)
    elif isinstance(value, datetime):
        return value.strftime(format)
    elif isinstance(value, str):
        try:
            # Try to parse the string as a datetime
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except:
            return datetime.now().strftime(format)
    else:
        return datetime.now().strftime(format)

@app.template_filter('average')
def average_filter(values):
    """Calculate average of a list of values."""
    try:
        if not values:
            return 0
        return sum(values) / len(values)
    except:
        return 0

# MongoDB Configuration - Direct URL (no environment variables)
app.config['MONGO_URI'] = 'mongodb+srv://ishan:ishan22399@website.8lfhad0.mongodb.net/?retryWrites=true&w=majority&appName=website'

# Initialize MongoDB connection with better error handling
client = None
db = None
collection = None
collection_info = None
register_collection = None
signuserinfo_collection = None

try:
    # Enhanced MongoDB connection with proper configuration
    client = MongoClient(app.config['MONGO_URI'], 
                        serverSelectionTimeoutMS=10000,  # 10 second timeout
                        connectTimeoutMS=10000,
                        socketTimeoutMS=10000,
                        retryWrites=True,
                        retryReads=True)
    
    # Test the connection
    client.admin.command('ping')
    db = client['license_verification_db']  # Specify your database name
    collection = db['driver_license_data']  # Replace with your collection name
    collection_info = db['driver_info']
    register_collection = db['register_user_info']  # New collection
    signuserinfo_collection = db['login_info']
    print("✅ MongoDB connection successful!")
    print(f"📊 Connected to database: license_verification_db")
    print(f"🔗 Using direct MongoDB connection")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Please check your MongoDB connection and try again.")
    print("The application will continue with limited functionality.")
    
    # Create mock collections for development
    class MockCollection:
        def find(self, *args, **kwargs):
            class MockCursor:
                def sort(self, *args, **kwargs):
                    return self
                def limit(self, *args, **kwargs):
                    return self
                def __iter__(self):
                    return iter([])
                def __list__(self):
                    return []
            return MockCursor()
        
        def find_one(self, *args, **kwargs):
            return None
        
        def insert_one(self, *args, **kwargs):
            class MockResult:
                inserted_id = "mock_id"
            return MockResult()
        
        def count_documents(self, *args, **kwargs):
            return 0
        
        def update_one(self, *args, **kwargs):
            class MockResult:
                modified_count = 0
            return MockResult()
        
        def delete_one(self, *args, **kwargs):
            class MockResult:
                deleted_count = 0
            return MockResult()
    
    # Create a mock database dictionary for compatibility
    class MockDB:
        def __getitem__(self, key):
            return MockCollection()
    
    db = MockDB()
    collection = MockCollection()
    collection_info = MockCollection()
    register_collection = MockCollection()
    signuserinfo_collection = MockCollection()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

conn = sqlite3.connect('timing_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS verification_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loading_time REAL,
        processing_time REAL,
        matching_time REAL,
        total_time REAL
    )
''')
conn.commit()
conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(img, target_size=(160, 160)):
    return cv2.resize(img, target_size)

def extract_faces_and_compare(img1_path, img2_path):
    # Load images using face_recognition library
    img1 = face_recognition.load_image_file(img1_path)
    img2 = face_recognition.load_image_file(img2_path)

    # Find face locations in the images
    face_locations_img1 = face_recognition.face_locations(img1)
    face_locations_img2 = face_recognition.face_locations(img2)

    # If no faces are found, return a high flow value
    if not face_locations_img1 or not face_locations_img2:
        return float('inf')

    # Encode faces
    face_encodings_img1 = face_recognition.face_encodings(img1, face_locations_img1)
    face_encodings_img2 = face_recognition.face_encodings(img2, face_locations_img2)

    face_encodings_img1 = np.array(face_encodings_img1)
    face_encodings_img2 = np.array(face_encodings_img2)

    # Calculate the face distance
    face_distance = face_recognition.face_distance(face_encodings_img1, face_encodings_img2)

    # Use the average distance as the flow value
    total_flow = np.mean(face_distance)
    print(total_flow)

    return total_flow

def process_holder_image(img1_path, holder_data):
    img2_path = holder_data['image_path']

    # Check if the dimensions of the two images match
    if os.path.exists(img2_path):
        total_flow = extract_faces_and_compare(img1_path, img2_path)

        return holder_data, total_flow

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        cov = request.form.getlist('cov[]')
        data = {
            'name': request.form['name'],
            'gender': request.form['gender'],
            'dob': request.form['dob'],
            'country': request.form['country'],
            'state': request.form['state'],
            'city': request.form['city'],
            'address_line': request.form['address_line'],
            'landmark': request.form['landmark'],
            'pincode': request.form['pincode'],
            'dl_number': request.form['dl_number'],
            'doi': request.form['doi'],
            'issuing_authority': request.form['issuing_authority'],
            'vt': request.form['vt'],
            'cov': cov,  
        }
        
        # Handle image files
        image = request.files['image']
        license_image = request.files['license_image']

        if license_image:
            license_image.save(os.path.join(app.config['LICENSE_IMAGE_UPLOAD_FOLDER'], license_image.filename))
            data['license_image_path'] = os.path.join(app.config['LICENSE_IMAGE_UPLOAD_FOLDER'], license_image.filename)

        if image:
            image.save(os.path.join(app.config['HOLDER_IMAGE_UPLOAD_FOLDER'], image.filename))
            data['image_path'] = os.path.join(app.config['HOLDER_IMAGE_UPLOAD_FOLDER'], image.filename)
            
            # Use 'collection' for storing data in 'driver_license_data' collection
            db['driver_license_data'].insert_one(data)

            return redirect(url_for('thank_you'))

    return 'Error in form submission'

@app.route('/thank_you')
def thank_you():
    return render_template('thankyou.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login_page'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def register():
    print("\n" + "="*60)
    print("🔴 REGISTRATION FUNCTION CALLED")
    print("="*60)
    
    try:
        # Check if request has form data
        if not request.form:
            print("❌ No form data received!")
            flash('No form data received', 'error')
            return redirect(url_for('register_page'))
        
        # Debug: Print ALL form data
        print(f"📝 Raw form data: {dict(request.form)}")
        print(f"📝 Form keys: {list(request.form.keys())}")
        
        # Extract form data with detailed checking
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '').strip()
        
        print(f"📋 Extracted data:")
        print(f"   - Name: '{name}' (length: {len(name)})")
        print(f"   - Phone: '{phone}' (length: {len(phone)})")
        print(f"   - Email: '{email}' (length: {len(email)})")
        print(f"   - Role: '{role}' (length: {len(role)})")
        print(f"   - Password: {'*' * len(password)} (length: {len(password)})")
        print(f"   - Confirm Password: {'*' * len(confirm_password)} (length: {len(confirm_password)})")
        
        # Check for empty/missing fields
        missing_fields = []
        if not name: missing_fields.append('name')
        if not phone: missing_fields.append('phone')
        if not email: missing_fields.append('email')
        if not password: missing_fields.append('password')
        if not confirm_password: missing_fields.append('confirm_password')
        if not role: missing_fields.append('role')
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            print(f"❌ Validation error: {error_msg}")
            flash(error_msg, 'error')
            return redirect(url_for('register_page'))
        
        print("✅ All required fields present")
        
        # Validate password match
        if password != confirm_password:
            print("❌ Password mismatch error")
            flash('Password and confirm password do not match', 'error')
            return redirect(url_for('register_page'))
        
        print("✅ Passwords match")
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            print(f"❌ Invalid email format: {email}")
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('register_page'))
        
        print("✅ Email format valid")
        
        # Validate phone number
        if not phone.isdigit() or len(phone) != 10:
            print(f"❌ Invalid phone number: {phone}")
            flash('Please enter a valid 10-digit phone number', 'error')
            return redirect(url_for('register_page'))
        
        print("✅ Phone number valid")
        
        # Check if user already exists in MongoDB
        print("🔍 Checking for existing user...")
        try:
            existing_user = register_collection.find_one({'email': email})
            if existing_user:
                print(f"❌ User already exists with email: {email}")
                flash('User with this email already exists', 'error')
                return redirect(url_for('register_page'))
            print("✅ No existing user found")
        except Exception as db_error:
            print(f"❌ Database check error: {str(db_error)}")
            print(f"Error type: {type(db_error).__name__}")
            flash('Database connection error. Please try again.', 'error')
            return redirect(url_for('register_page'))
        
        # Hash password
        print("🔐 Hashing password...")
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            print("✅ Password hashed successfully")
        except Exception as hash_error:
            print(f"❌ Password hashing error: {str(hash_error)}")
            flash('Password processing error. Please try again.', 'error')
            return redirect(url_for('register_page'))
        
        # Create Firebase user
        print("🔥 Creating Firebase user...")
        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            uid = user.uid
            print(f"✅ Firebase user created with UID: {uid}")
        except Exception as firebase_error:
            print(f"❌ Firebase user creation error: {str(firebase_error)}")
            print(f"Error type: {type(firebase_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Check for specific error types
            error_str = str(firebase_error).lower()
            if "email_exists" in error_str or "already exists" in error_str:
                flash('An account with this email exists', 'error')
            elif "invalid_email" in error_str:
                flash('Invalid email address format', 'error')
            elif "weak_password" in error_str:
                flash('Password is too weak. Please use a stronger password.', 'error')
            else:
                flash(f'Account creation failed: {str(firebase_error)}', 'error')
            return redirect(url_for('register_page'))
        
        # Prepare user data
        print("📝 Preparing user data...")
        try:
            user_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "password": hashed_password,
                "uid": uid,
                "role": role,
                "created_at": datetime.now(pytz.timezone('Asia/Kolkata'))
            }
            print(f"✅ User data prepared: {dict((k, v if k != 'password' else '*****') for k, v in user_data.items())}")
        except Exception as data_error:
            print(f"❌ Data preparation error: {str(data_error)}")
            flash('Data processing error. Please try again.', 'error')
            return redirect(url_for('register_page'))
        
        # Insert into MongoDB
        print("💾 Inserting user into MongoDB...")
        try:
            result = register_collection.insert_one(user_data)
            print(f"✅ MongoDB insert successful. ID: {result.inserted_id}")
        except Exception as mongo_error:
            print(f"❌ MongoDB insert error: {str(mongo_error)}")
            print(f"Error type: {type(mongo_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Try to delete the Firebase user if MongoDB fails
            try:
                auth.delete_user(uid)
                print("🧹 Firebase user deleted due to MongoDB error")
            except Exception as cleanup_error:
                print(f"❌ Failed to cleanup Firebase user: {str(cleanup_error)}")
            
            flash('Database error during registration. Please try again.', 'error')
            return redirect(url_for('register_page'))
        
        # Insert into Firebase Realtime Database
        print("🔥 Inserting user into Firebase Database...")
        try:
            # Convert datetime to string for Firebase
            firebase_data = user_data.copy()
            firebase_data['created_at'] = user_data['created_at'].isoformat()
            
            firebase_db.child("users").child(uid).set(firebase_data)
            print("✅ Firebase Database insert successful")
        except Exception as firebase_db_error:
            print(f"⚠️ Firebase Database error: {str(firebase_db_error)}")
            print("Note: Registration will continue as MongoDB insert was successful")
        
        print("🎉 Registration completed successfully!")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login_page'))
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR in registration:")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        flash(f'Registration failed due to server error: {str(e)}', 'error')
        return redirect(url_for('register_page'))
    
    finally:
        print("="*60)
        print("🔴 REGISTRATION FUNCTION END")
        print("="*60 + "\n")

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    try:
        user = auth.get_user_by_email(email)
        uid = user.uid

        user_data = register_collection.find_one({'uid': uid})
        if user_data and check_password_hash(user_data.get('password'), password):
            # Set session data
            session['user_id'] = str(user_data['_id'])
            session['user_email'] = email
            session['user_name'] = user_data.get('name')
            session['role'] = user_data.get('role', 'user')
            session['uid'] = uid

            ist = pytz.timezone('Asia/Kolkata')
            login_time = datetime.now(ist)

            login_info = {
                'email': email,
                'timestamp': login_time,
                'uid': uid
            }

            signuserinfo_collection.insert_one(login_info)

            flash(f'Welcome {user_data.get("name")}!', 'success')
            
            # Redirect based on role
            if user_data.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login_page'))

    except auth.UserNotFoundError:
        flash('User not found', 'error')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('login_page'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect based on role
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get user's verification history
    user_verifications = signuserinfo_collection.find({'email': session['user_email']}).sort('timestamp', -1)
    return render_template('user_dashboard.html', 
                         user_name=session['user_name'],
                         verifications=list(user_verifications))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Get statistics for admin with error handling
        total_users = 0
        total_licenses = 0
        total_verifications = 0
        recent_users = []
        recent_logins = []
        
        if register_collection is not None and hasattr(register_collection, 'count_documents'):
            try:
                total_users = register_collection.count_documents({})
            except Exception as e:
                print(f"Error getting user count: {e}")
                total_users = 0
        
        if collection is not None and hasattr(collection, 'count_documents'):
            try:
                total_licenses = collection.count_documents({})
            except Exception as e:
                print(f"Error getting license count: {e}")
                total_licenses = 0
        
        if signuserinfo_collection is not None and hasattr(signuserinfo_collection, 'count_documents'):
            try:
                total_verifications = signuserinfo_collection.count_documents({})
            except Exception as e:
                print(f"Error getting verification count: {e}")
                total_verifications = 0
        
        # Recent activities with error handling
        if register_collection is not None and hasattr(register_collection, 'find'):
            try:
                recent_users = list(register_collection.find({}).sort('created_at', -1).limit(5))
            except Exception as e:
                print(f"Error getting recent users: {e}")
                recent_users = []
        
        if signuserinfo_collection is not None and hasattr(signuserinfo_collection, 'find'):
            try:
                recent_logins = list(signuserinfo_collection.find({}).sort('timestamp', -1).limit(10))
            except Exception as e:
                print(f"Error getting recent logins: {e}")
                recent_logins = []
        
        # Convert ObjectId to string for JSON serialization
        for user in recent_users:
            if '_id' in user:
                user['_id'] = str(user['_id'])
        
        return render_template('admin_dashboard.html',
                             admin_name=session.get('user_name', 'Admin'),
                             total_users=total_users,
                             total_licenses=total_licenses,
                             total_verifications=total_verifications,
                             recent_users=recent_users,
                             recent_logins=recent_logins)
    except Exception as e:
        print(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard data. Running in offline mode.', 'warning')
        return render_template('admin_dashboard.html',
                             admin_name=session.get('user_name', 'Admin'),
                             total_users=0,
                             total_licenses=0,
                             total_verifications=0,
                             recent_users=[],
                             recent_logins=[])

@app.route('/admin/users')
@admin_required
def admin_users():
    try:
        # Get all users from database
        users = list(register_collection.find({}))
        
        # Convert ObjectId to string for template rendering
        for user in users:
            user['_id'] = str(user['_id'])
        
        # Calculate statistics
        total_users = len(users)
        active_users = len([u for u in users if u.get('status', 'active') == 'active'])
        admin_users = len([u for u in users if u.get('role') == 'admin'])
        
        # Get new users this month
        from datetime import datetime, timedelta
        current_month = datetime.now().replace(day=1)
        new_users = len([u for u in users if u.get('created_at') and u['created_at'] >= current_month])
        
        return render_template('admin_users.html', 
                             users=users,
                             total_users=total_users,
                             active_users=active_users,
                             admin_users=admin_users,
                             new_users=new_users)
    except Exception as e:
        print(f"Error in admin_users: {str(e)}")
        flash('Error loading user data', 'error')
        return render_template('admin_users.html', 
                             users=[],
                             total_users=0,
                             active_users=0,
                             admin_users=0,
                             new_users=0)

@app.route('/admin/licenses')
@admin_required
def admin_licenses():
    try:
        # Get all licenses from database
        licenses = list(collection.find({}))
        
        # Convert ObjectId to string for template rendering
        for license in licenses:
            license['_id'] = str(license['_id'])
        
        # Calculate statistics
        total_licenses = len(licenses)
        verified_licenses = total_licenses  # All licenses are verified by default
        pending_licenses = 0  # No pending system implemented yet
        rejected_licenses = 0  # No rejection system implemented yet
        today_licenses = 0  # Would need to filter by today's date
        expiring_licenses = 0  # Would need to check expiry dates
        
        return render_template('admin_licenses.html', 
                             licenses=licenses,
                             total_licenses=total_licenses,
                             verified_licenses=verified_licenses,
                             pending_licenses=pending_licenses,
                             rejected_licenses=rejected_licenses,
                             today_licenses=today_licenses,
                             expiring_licenses=expiring_licenses)
    except Exception as e:
        print(f"Error in admin_licenses: {str(e)}")
        flash('Error loading license data', 'error')
        return render_template('admin_licenses.html', 
                             licenses=[],
                             total_licenses=0,
                             verified_licenses=0,
                             pending_licenses=0,
                             rejected_licenses=0,
                             today_licenses=0,
                             expiring_licenses=0)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    try:
        # Get analytics data for reports
        conn = sqlite3.connect('timing_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM verification_data ORDER BY id DESC LIMIT 100')
        verification_data = cursor.fetchall()
        conn.close()
        
        # Get verification logs
        verification_logs = list(db['verification_logs'].find({}).sort('verification_time', -1).limit(50))
        
        return render_template('admin_reports.html',
                             verification_data=verification_data,
                             verification_logs=verification_logs)
    except Exception as e:
        print(f"Error in admin_reports: {str(e)}")
        flash('Error loading reports data', 'error')
        return render_template('admin_reports.html',
                             verification_data=[],
                             verification_logs=[])

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin_settings.html')

# Add datetime objects to template context
@app.context_processor
def inject_datetime():
    return {
        'datetime': datetime,
        'timedelta': timedelta
    }

# API routes for admin operations
@app.route('/api/admin/user/<user_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def admin_user_operations(user_id):
    try:
        if request.method == 'GET':
            user = register_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                return jsonify({'success': True, 'user': user})
            else:
                return jsonify({'success': False, 'message': 'User not found'})
        
        elif request.method == 'PUT':
            # Update user
            update_data = request.json
            result = register_collection.update_one(
                {'_id': ObjectId(user_id)}, 
                {'$set': update_data}
            )
            if result.modified_count > 0:
                return jsonify({'success': True, 'message': 'User updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'User not found or no changes made'})
        
        elif request.method == 'DELETE':
            # Delete user (soft delete - update status)
            result = register_collection.update_one(
                {'_id': ObjectId(user_id)}, 
                {'$set': {'status': 'deleted', 'deleted_at': datetime.now()}}
            )
            if result.modified_count > 0:
                return jsonify({'success': True, 'message': 'User deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'User not found'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/license/<license_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def admin_license_operations(license_id):
    try:
        if request.method == 'GET':
            license = collection.find_one({'_id': ObjectId(license_id)})
            if license:
                license['_id'] = str(license['_id'])
                return jsonify({'success': True, 'license': license})
            else:
                return jsonify({'success': False, 'message': 'License not found'})
        
        elif request.method == 'PUT':
            # Update license
            update_data = request.json
            result = collection.update_one(
                {'_id': ObjectId(license_id)}, 
                {'$set': update_data}
            )
            if result.modified_count > 0:
                return jsonify({'success': True, 'message': 'License updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'License not found or no changes made'})
        
        elif request.method == 'DELETE':
            # Delete license
            result = collection.delete_one({'_id': ObjectId(license_id)})
            if result.deleted_count > 0:
                return jsonify({'success': True, 'message': 'License deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'License not found'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    try:
        # Get real-time statistics
        total_users = register_collection.count_documents({})
        total_licenses = collection.count_documents({})
        total_verifications = signuserinfo_collection.count_documents({})
        
        # Get today's statistics
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = register_collection.count_documents({'created_at': {'$gte': today}})
        today_verifications = signuserinfo_collection.count_documents({'timestamp': {'$gte': today}})
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_licenses': total_licenses,
                'total_verifications': total_verifications,
                'today_users': today_users,
                'today_verifications': today_verifications
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/license')
@login_required
def license():
    return render_template('license.html')

@app.route('/verification')
@login_required
def verification():
    return render_template('verification_page.html')

@app.route('/analytics')
@admin_required
def analytics():
    # Get analytics data from SQLite
    conn = sqlite3.connect('timing_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM verification_data ORDER BY id DESC LIMIT 100')
    analytics_data = cursor.fetchall()
    conn.close()
    
    return render_template('analytics.html', analytics_data=analytics_data)

@app.route('/complaint')
@login_required
def complaint():
    return render_template('complaint.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'driverImage' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})

    image_file = request.files['driverImage']

    if image_file:
        # Read the image from the stream
        nparr = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Access the camera
        cap = cv2.VideoCapture(0)  # Use the default camera (index 0)

        # Capture frame-by-frame
        ret, frame = cap.read()

        if ret:
            # Generate a unique filename or use a timestamp as filename
            timestamp = time.strftime("%Y%m%d%H%M%S")
            image_filename = f"camera_capture_{timestamp}.jpg"

            # Save the image
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            cv2.imwrite(image_path, frame)

            # Release the camera
            cap.release()

            # Store the image path in MongoDB along with other data
            data = {
                'image_path': image_path,
            }

            db['driver_info'].insert_one(data)

            return jsonify({'success': True, 'message': 'Image uploaded successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to capture image from camera'})
    else:
        return jsonify({'success': False, 'message': 'Invalid file format'})

@app.route('/verify', methods=['POST'])
@login_required
def verify():
    start_time = time.time()
    print("")

    if 'driverImage' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})

    image_file = request.files['driverImage']
    if image_file and allowed_file(image_file.filename):
        image_filename = os.path.splitext(image_file.filename)[0]
        img1_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{image_filename}.jpg')
        image_file.save(img1_path)

        try:
            # Compute encoding for uploaded image
            uploaded_encoding = compute_face_encoding(img1_path)
            if uploaded_encoding is None:
                return jsonify({'success': False, 'message': 'No face detected in uploaded image'})

            # Fetch all license encodings from DB
            license_docs = list(collection.find({'face_encoding': {'$exists': True}}))
            if not license_docs:
                return jsonify({'success': False, 'message': 'No indexed license data available for verification'})

            # Prepare numpy arrays for fast comparison
            encodings_matrix = np.array([doc['face_encoding'] for doc in license_docs])
            uploaded_encoding_np = np.array(uploaded_encoding)

            # Vectorized face distance calculation
            face_distances = face_recognition.face_distance(encodings_matrix, uploaded_encoding_np)
            best_idx = np.argmin(face_distances)
            best_match_flow = face_distances[best_idx]
            best_match_data = license_docs[best_idx]

            loading_time = time.time() - start_time
            processing_time = loading_time  # For this approach, loading and processing are combined
            matching_time = 0  # Negligible due to vectorization
            print("Loading/Processing Time:", loading_time)
            print("Best match flow:", best_match_flow)

            threshold = 0.6
            if best_match_flow < threshold:
                # Remove sensitive fields if needed
                best_match_data.pop('face_encoding', None)
                best_match_data.pop('_id', None)
                total_time = time.time() - start_time

                # Store timing info in SQLite
                try:
                    conn = sqlite3.connect('timing_data.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO verification_data (loading_time, processing_time, matching_time, total_time)
                        VALUES (?, ?, ?, ?)
                    ''', (loading_time, processing_time, matching_time, total_time))
                    conn.commit()
                    conn.close()
                except Exception as sqlite_error:
                    print(f"SQLite error: {sqlite_error}")

                # Log verification attempt
                try:
                    verification_log = {
                        'user_id': session.get('user_id'),
                        'user_email': session.get('user_email'),
                        'verification_time': datetime.now(pytz.timezone('Asia/Kolkata')),
                        'success': True,
                        'license_verified': best_match_data.get('dl_number', 'Unknown'),
                        'processing_time': total_time
                    }
                    if hasattr(db, '__getitem__'):
                        db['verification_logs'].insert_one(verification_log)
                except Exception as log_error:
                    print(f"Logging error: {log_error}")

                return jsonify({
                    'success': True,
                    'message': 'Verification Successful!',
                    'data': best_match_data,
                })
            else:
                # Log failed verification
                try:
                    verification_log = {
                        'user_id': session.get('user_id'),
                        'user_email': session.get('user_email'),
                        'verification_time': datetime.now(pytz.timezone('Asia/Kolkata')),
                        'success': False,
                        'match_score': float(best_match_flow)
                    }
                    if hasattr(db, '__getitem__'):
                        db['verification_logs'].insert_one(verification_log)
                except Exception as log_error:
                    print(f"Logging error: {log_error}")

                return jsonify({'success': False, 'message': 'User not found', 'best_match_flow': float(best_match_flow)})
        except Exception as e:
            print(f"Verification error: {str(e)}")
            return jsonify({'success': False, 'message': f'Verification failed: {str(e)}'})

    else:
        return jsonify({'success': False, 'message': 'Invalid file format'})

def compute_face_encoding(image_path):
    """Compute face encoding for a given image path."""
    img = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(img)
    if not face_locations:
        return None
    encodings = face_recognition.face_encodings(img, face_locations)
    if encodings:
        return encodings[0].tolist()  # Convert numpy array to list for MongoDB
    return None

def index_all_license_encodings():
    """Precompute and store face encodings for all licenses in the DB."""
    updated = 0
    for license_doc in collection.find({}):
        if 'image_path' in license_doc and 'face_encoding' not in license_doc:
            encoding = compute_face_encoding(license_doc['image_path'])
            if encoding is not None:
                collection.update_one(
                    {'_id': license_doc['_id']},
                    {'$set': {'face_encoding': encoding}}
                )
                updated += 1
    print(f"Indexed {updated} license face encodings.")

# Optionally, call this at startup (or run as a separate script/endpoint)
index_all_license_encodings()

@app.route('/admin/index-encodings')
@admin_required
def admin_index_encodings():
    index_all_license_encodings()
    flash('License face encodings indexed successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/user/verification-history')
@login_required
def user_verification_history():
    try:
        # Get user's verification history from multiple sources
        user_email = session.get('user_email')
        user_id = session.get('user_id')
        
        # Get verification logs from MongoDB
        verification_logs = []
        if db is not None and hasattr(db, '__getitem__'):
            try:
                logs = list(db['verification_logs'].find({
                    '$or': [
                        {'user_email': user_email},
                        {'user_id': user_id}
                    ]
                }).sort('verification_time', -1).limit(100))
                verification_logs = logs
            except Exception as e:
                print(f"Error fetching verification logs: {e}")
        
        # Get login history (as verification activity)
        login_history = []
        if signuserinfo_collection is not None:
            try:
                logins = list(signuserinfo_collection.find({
                    'email': user_email
                }).sort('timestamp', -1).limit(50))
                login_history = logins
            except Exception as e:
                print(f"Error fetching login history: {e}")
        
        # Calculate statistics
        total_verifications = len(verification_logs)
        successful_verifications = len([log for log in verification_logs if log.get('success', False)])
        failed_verifications = total_verifications - successful_verifications
        
        # Recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_verifications = [
            log for log in verification_logs 
            if log.get('verification_time') and log['verification_time'] >= thirty_days_ago
        ]
        
        # Calculate success rate
        success_rate = (successful_verifications / total_verifications * 100) if total_verifications > 0 else 0
        
        # Convert ObjectId to string for template rendering
        for log in verification_logs:
            if '_id' in log:
                log['_id'] = str(log['_id'])
        
        for login in login_history:
            if '_id' in login:
                login['_id'] = str(login['_id'])
        
        return render_template('user_verification_history.html',
                             verification_logs=verification_logs,
                             login_history=login_history,
                             total_verifications=total_verifications,
                             successful_verifications=successful_verifications,
                             failed_verifications=failed_verifications,
                             recent_verifications=len(recent_verifications),
                             success_rate=round(success_rate, 1),
                             user_name=session.get('user_name', 'User'))
        
    except Exception as e:
        print(f"Error in user_verification_history: {str(e)}")
        flash('Error loading verification history', 'error')
        return render_template('user_verification_history.html',
                             verification_logs=[],
                             login_history=[],
                             total_verifications=0,
                             successful_verifications=0,
                             failed_verifications=0,
                             recent_verifications=0,
                             success_rate=0,
                             user_name=session.get('user_name', 'User'))

@app.route('/admin/verification-history')
@admin_required
def admin_verification_history():
    try:
        # Get all verification logs for admin view
        verification_logs = []
        if db is not None and hasattr(db, '__getitem__'):
            try:
                logs = list(db['verification_logs'].find({}).sort('verification_time', -1).limit(500))
                verification_logs = logs
            except Exception as e:
                print(f"Error fetching verification logs: {e}")
        
        # Get all users for filtering
        all_users = []
        if register_collection is not None:
            try:
                users = list(register_collection.find({}, {'_id': 1, 'name': 1, 'email': 1}))
                all_users = users
            except Exception as e:
                print(f"Error fetching users: {e}")
        
        # Calculate comprehensive statistics
        total_verifications = len(verification_logs)
        successful_verifications = len([log for log in verification_logs if log.get('success', False)])
        failed_verifications = total_verifications - successful_verifications
        
        # Today's statistics
        from datetime import datetime, timedelta
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_verifications = [
            log for log in verification_logs 
            if log.get('verification_time') and log['verification_time'] >= today
        ]
        today_successful = len([log for log in today_verifications if log.get('success', False)])
        
        # This week's statistics
        week_ago = datetime.now() - timedelta(days=7)
        week_verifications = [
            log for log in verification_logs 
            if log.get('verification_time') and log['verification_time'] >= week_ago
        ]
        
        # User-wise statistics
        user_stats = {}
        for log in verification_logs:
            user_email = log.get('user_email', 'Unknown')
            if user_email not in user_stats:
                user_stats[user_email] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'last_activity': None
                }
            
            user_stats[user_email]['total'] += 1
            if log.get('success', False):
                user_stats[user_email]['successful'] += 1
            else:
                user_stats[user_email]['failed'] += 1
            
            # Update last activity
            if log.get('verification_time'):
                if not user_stats[user_email]['last_activity'] or log['verification_time'] > user_stats[user_email]['last_activity']:
                    user_stats[user_email]['last_activity'] = log['verification_time']
        
        # Convert to list for easier template handling
        user_stats_list = []
        for email, stats in user_stats.items():
            stats['email'] = email
            stats['success_rate'] = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            user_stats_list.append(stats)
        
        # Sort by total verifications
        user_stats_list.sort(key=lambda x: x['total'], reverse=True)
        
        # Calculate overall success rate
        success_rate = (successful_verifications / total_verifications * 100) if total_verifications > 0 else 0
        
        # Convert ObjectId to string for template rendering
        for log in verification_logs:
            if '_id' in log:
                log['_id'] = str(log['_id'])
        
        for user in all_users:
            if '_id' in user:
                user['_id'] = str(user['_id'])
        
        return render_template('admin_verification_history.html',
                             verification_logs=verification_logs,
                             all_users=all_users,
                             user_stats=user_stats_list,
                             total_verifications=total_verifications,
                             successful_verifications=successful_verifications,
                             failed_verifications=failed_verifications,
                             today_verifications=len(today_verifications),
                             today_successful=today_successful,
                             week_verifications=len(week_verifications),
                             success_rate=round(success_rate, 1),
                             admin_name=session.get('user_name', 'Admin'))
        
    except Exception as e:
        print(f"Error in admin_verification_history: {str(e)}")
        flash('Error loading verification history', 'error')
        return render_template('admin_verification_history.html',
                             verification_logs=[],
                             all_users=[],
                             user_stats=[],
                             total_verifications=0,
                             successful_verifications=0,
                             failed_verifications=0,
                             today_verifications=0,
                             today_successful=0,
                             week_verifications=0,
                             success_rate=0,
                             admin_name=session.get('user_name', 'Admin'))

@app.route('/api/admin/verification-history/user/<user_email>')
@admin_required
def admin_user_verification_history(user_email):
    try:
        # Get specific user's verification history
        user_logs = []
        if db is not None and hasattr(db, '__getitem__'):
            logs = list(db['verification_logs'].find({
                'user_email': user_email
            }).sort('verification_time', -1))
            
            # Convert ObjectId to string
            for log in logs:
                if '_id' in log:
                    log['_id'] = str(log['_id'])
                # Convert datetime to string for JSON serialization
                if 'verification_time' in log and hasattr(log['verification_time'], 'isoformat'):
                    log['verification_time'] = log['verification_time'].isoformat()
            
            user_logs = logs
        
        return jsonify({
            'success': True,
            'logs': user_logs,
            'total': len(user_logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/office-directory')
@login_required
def office_directory():
    try:
        # In a real application, this would fetch data from a database
        # For now, we'll provide some sample statistics
        office_stats = {
            'total_offices': 156,
            'nearby_offices': 12,
            'open_offices': 89,
            'avg_distance': '3.2'
        }
        
        return render_template('office_directory.html', **office_stats)
    except Exception as e:
        print(f"Error in office_directory: {str(e)}")
        flash('Error loading office directory', 'error')
        return render_template('office_directory.html', 
                             total_offices=0,
                             nearby_offices=0,
                             open_offices=0,
                             avg_distance='0')

@app.route('/api/offices/search')
@login_required
def search_offices_api():
    try:
        # Get search parameters
        location = request.args.get('location', '').strip()
        state = request.args.get('state', '').strip()
        service = request.args.get('service', '').strip()
        
        # In a real application, this would query a database
        # For now, return sample data
        sample_offices = [
            {
                'id': 1,
                'name': 'RTO Mumbai Central',
                'code': 'MH-01',
                'address': '123 Central Road, Mumbai, Maharashtra - 400001',
                'phone': '+91 22 2267 1234',
                'email': 'rto.mumbai@mh.gov.in',
                'distance': 2.1,
                'status': 'open',
                'services': ['New License', 'Renewal', 'Vehicle Registration', 'Duplicate License'],
                'timings': {
                    'weekdays': '10:00 AM - 6:00 PM',
                    'saturday': '10:00 AM - 2:00 PM',
                    'sunday': 'Closed'
                }
            },
            {
                'id': 2,
                'name': 'RTO Andheri West',
                'code': 'MH-02',
                'address': '456 SV Road, Andheri West, Mumbai - 400058',
                'phone': '+91 22 2634 5678',
                'email': 'rto.andheri@mh.gov.in',
                'distance': 4.8,
                'status': 'closed',
                'services': ['License Renewal', 'Fitness Certificate', 'NOC', 'International Permit'],
                'timings': {
                    'weekdays': '10:00 AM - 5:30 PM',
                    'saturday': '10:00 AM - 1:00 PM',
                    'sunday': 'Closed'
                }
            }
        ]
        
        # Apply basic filtering
        filtered_offices = []
        for office in sample_offices:
            include = True
            
            if location:
                office_text = f"{office['name']} {office['address']}".lower()
                include = include and location.lower() in office_text
            
            if state:
                include = include and state.lower() in office['address'].lower()
            
            if service:
                service_match = any(service.lower().replace('-', ' ') in s.lower() for s in office['services'])
                include = include and service_match
            
            if include:
                filtered_offices.append(office)
        
        return jsonify({
            'success': True,
            'offices': filtered_offices,
            'total': len(filtered_offices)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)


