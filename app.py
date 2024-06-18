import os
import multiprocessing
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import cv2
import sqlite3
import numpy as np
import face_recognition
from functools import partial
import time
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import db
from werkzeug.security import generate_password_hash
from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from pytz import timezone
import pytz

UPLOAD_FOLDER = 'uploads/driver_images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}  # Add your allowed extensions

cred = credentials.Certificate("firebase-adminsdk.json") # Firebase Admin SDK JSON File
firebase_admin.initialize_app(cred, {
    'databaseURL': ' ' # Firebase Database URL
})
firebase_db = db.reference()


app = Flask(__name__)
app.secret_key = 'stark'  # Replace with a secure secret key
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['LICENSE_IMAGE_UPLOAD_FOLDER'] = 'uploads/license_images'
app.config['HOLDER_IMAGE_UPLOAD_FOLDER'] = 'uploads/holder_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MONGO_URI'] = ' '  # Replace with your MongoDB URI and database name

client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()
collection = db['driver_license_data']  # Replace with your collection name
collection_info = db['driver_info']
register_collection = db['register_user_info']  # New collection
signuserinfo_collection = db['login_info']

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

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    phone = request.form['fa-phone']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        return "Password and confirm password do not match"

    try:
        # Stronger password hashing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Create user in Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password
        )

        # Get the UID from the Firebase user object
        uid = user.uid

        # Save user data to MongoDB with UID
        user_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "password": hashed_password,
            "uid": uid  # Add UID to user data
        }
        result = register_collection.insert_one(user_data)

        # Save additional user data (including UID) to Firebase Realtime Database
        firebase_db.child("users").child(uid).set(user_data)

        return redirect("/login")  # Redirect to login page after successful registration
    except Exception as e:
        # If an error occurs, redirect to the login page without showing any error message
        return redirect("/login")
    
@app.route('/dashboard')
def dashboard():
    # Add your dashboard logic here
    return render_template('admin_login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    try:
        # Retrieve the user's UID from Firebase Authentication using their email
        user = auth.get_user_by_email(email)
        uid = user.uid

        # Check if the UID exists in the MongoDB collection
        user_data = register_collection.find_one({'uid': uid})
        if user_data:
            # Retrieve the corresponding password hash from MongoDB
            stored_password_hash = user_data.get('password')
            
            # Hash the password provided during login
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Compare the hashed passwords
            if check_password_hash(stored_password_hash, password):
                # Get the current time in Indian Standard Time (IST)
                ist = pytz.timezone('Asia/Kolkata')
                login_time = datetime.now(ist)

                # Create a document to store in MongoDB
                login_info = {
                    'email': email,
                    'timestamp': login_time
                }

                # Store the login information in the 'signuserinfo' collection
                signuserinfo_collection.insert_one(login_info)

                return redirect(url_for('dashboard'))
            else:
                return "Login failed. Incorrect password."
        else:
            return "Login failed. User not found."

    except auth.UserNotFoundError:
        return "Login failed. User not found."


@app.route('/admin')
def admin_page():
    return render_template('admin_login.html')

@app.route('/license')
def license():
    return render_template('license.html')

@app.route('/verification')
def verification():
    return render_template('verification_page.html')


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
def verify():
    start_time = time.time()
    print("")


    if 'driverImage' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})

    image_file = request.files['driverImage']
    if image_file and allowed_file(image_file.filename):
        image_filename = os.path.splitext(image_file.filename)[0]

        # Save the image with its original extension
        img1_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{image_filename}.jpg')
        image_file.save(img1_path)

      

        # Retrieve the holder images from the 'driver_license_data' collection
        holder_images_paths = [holder_data['image_path'] for holder_data in
                              db['driver_license_data'].find({}, {'_id': 0, 'image_path': 1})]
        
        loading_time = time.time() - start_time 
        print("Loading Time:", loading_time)


        # Use multiprocessing to process the holder images in parallel
        with multiprocessing.Pool() as pool:
            holder_data_flows = pool.map(partial(extract_faces_and_compare, img1_path), holder_images_paths)

            processing_time = time.time() - start_time - loading_time  # Calculate the time taken for processing
            print("Processing Time:", processing_time)

        # Combine holder data and their respective optical flow values
        holder_data_with_flows = zip(db['driver_license_data'].find({}, {'_id': 0, 'image_path': 1}), holder_data_flows)

        # Identify the holder with the lowest optical flow value (best match)
        best_match_data, best_match_flow = min(holder_data_with_flows, key=lambda x: x[1])

        matching_time = time.time() - start_time - loading_time - processing_time  # Calculate the time taken for matching
        print("Matching Time:", matching_time)
        # Check if the best match flow is below the threshold
        
        threshold = 0.6
        if best_match_flow < threshold:
            best_match_data = db['driver_license_data'].find_one({'image_path': best_match_data['image_path']}, {'_id': 0})
            total_time = time.time() - start_time  # Calculate the total verification time
            print("Total Time:", total_time)

            # Store the timing information in SQLite database
            conn = sqlite3.connect('timing_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO verification_data (loading_time, processing_time, matching_time, total_time)
                VALUES (?, ?, ?, ?)
            ''', (loading_time, processing_time, matching_time, total_time))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Verification Successful!',
                'data': best_match_data,
                
            })
        else:
            return jsonify({'success': False, 'message': 'User not found', 'best_match_flow': best_match_flow})

    else:
        return jsonify({'success': False, 'message': 'Invalid file format'})

if __name__ == '__main__':
    app.run(debug=True)


