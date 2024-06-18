let videoStream;
document.getElementById('verificationForm').addEventListener('submit', function (event) {
    event.preventDefault();

    var formData = new FormData(this);

    fetch('/verify', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.result === 'success') {
            document.getElementById('result').innerHTML = 'Verification successful. Driver details: ' + data.name;
        } else {
            document.getElementById('result').innerHTML = '<span style="color: red; font-weight: bold;">User not found.</span>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function captureImage() {
    // Access the user's camera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
            videoStream = stream;

            // Create a video element to display the camera feed
            const video = document.createElement('video');
            video.setAttribute('autoplay', 'true');
            video.srcObject = stream;

            // Display the video in a modal or a separate window
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            modal.appendChild(video);
            document.body.appendChild(modal);

            // Add capture and retake buttons
            const captureButton = document.createElement('button');
            captureButton.textContent = 'Capture';
            captureButton.addEventListener('click', () => {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

                const imageUrl = canvas.toDataURL('image/png');
                videoStream.getTracks().forEach(track => track.stop());
                document.body.removeChild(modal);

                // TODO: Upload the captured image (imageUrl) for verification
                // You may use the Fetch API to send the image data to the server
                // Example: fetch('/upload', { method: 'POST', body: imageUrl });


                // Upload the captured image for verification
                fetch('/verify', {
                    method: 'POST',
                    body: JSON.stringify({ image: imageUrl }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.result === 'success') {
                        document.getElementById('result').innerHTML = 'Verification successful. Driver details: ' + data.name;
                    } else {
                        document.getElementById('result').innerHTML = '<span style="color: red; font-weight: bold;">User not found.</span>';
                    }
                })
                .catch(error => {
                    console.error('Error uploading image:', error);
                });
            });
            

            const retakeButton = document.createElement('button');
            retakeButton.textContent = 'Retake';
            retakeButton.addEventListener('click', () => {
                videoStream.getTracks().forEach(track => track.stop());
                document.body.removeChild(modal);
            });

            modal.appendChild(captureButton);
            modal.appendChild(retakeButton);
        })
        .catch((error) => {
            console.error('Error accessing camera:', error);
        });
}

