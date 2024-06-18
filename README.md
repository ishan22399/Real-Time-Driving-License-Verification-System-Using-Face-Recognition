# Real-Time Driving License Verification System Using Face Recognition

## Overview

This project implements a real-time system for verifying driving licenses using face recognition technology. The system captures live video from a camera, detects faces, and matches them against a database of authorized users to verify the authenticity of the driver's license. The goal is to enhance security and ensure that only authorized individuals can use a particular driving license.

## Features

- **Real-time face detection**: Captures live video and detects faces in real-time.
- **Face recognition**: Matches detected faces with a pre-stored database of authorized users.
- **Database integration**: Connects to both MongoDB and Firebase for storing user data.
- **User-friendly interface**: Provides a simple interface for users to interact with the system.
- **High accuracy**: Utilizes advanced face recognition algorithms for high accuracy in verification.
- **Registration and login**: Allows users to register and log in securely.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Real-Time-Driving-License-Verification-System-Using-Face-Recognition.git
    cd Real-Time-Driving-License-Verification-System-Using-Face-Recognition
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the database**:
    - **MongoDB**: Ensure you have MongoDB installed and running. Replace the MongoDB URI in `app.config['MONGO_URI']` with your MongoDB URI.
    - **Firebase**: Place your Firebase Admin SDK JSON file in the project directory and configure the Firebase database URL in `firebase_admin.initialize_app`.

4. **Run the application**:
    ```bash
    python app.py
    ```

## Configuration

- **UPLOAD_FOLDER**: Directory for storing uploaded images.
- **ALLOWED_EXTENSIONS**: Set of allowed file extensions for uploads.
- **MongoDB URI**: Replace `app.config['MONGO_URI']` with your MongoDB URI.
- **Firebase**: Update the Firebase configuration with your Firebase Admin SDK JSON file and database URL.

## Usage

1. **Start the application**:
    - Run the `app.py` script to start the system.
    - The system will activate the camera and begin capturing video.

2. **Face detection and recognition**:
    - The system will detect faces in the video feed.
    - Detected faces will be compared against the database to verify the identity.

3. **Registration**:
    - Users can register by providing their information and uploading images.
    - Registration data is stored in MongoDB and Firebase.

4. **Login**:
    - Users can log in using their email and password.
    - Login data is verified using Firebase Authentication.

5. **Verification**:
    - Users can upload a driver's image for verification.
    - The system compares the uploaded image with the database and returns the verification result.

## Reference

For more detailed information on the implementation and underlying technology, refer to the published paper:
- [Real-Time Driving License Verification System Using Face Recognition](https://doi.org/10.36227/techrxiv.171863959.94854977/v1)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
