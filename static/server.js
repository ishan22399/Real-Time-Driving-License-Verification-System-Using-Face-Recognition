const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const path = require('path');
const app = express();

// Connect to MongoDB (make sure MongoDB is running)
mongoose.connect('mongodb://localhost/imageUploadDB', { useNewUrlParser: true, useUnifiedTopology: true });

// Create a schema and model for storing image data
const ImageSchema = new mongoose.Schema({
    name: String,
    data: Buffer,
    contentType: String,
});

const Image = mongoose.model('Image', ImageSchema);

// Configure multer for image upload
const storage = multer.memoryStorage(); // Store the image in memory
const upload = multer({ storage: storage });

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Handle image upload
app.post('/upload', upload.single('image'), async (req, res) => {
    try {
        const { originalname, buffer, mimetype } = req.file;
        const image = new Image({
            name: originalname,
            data: buffer,
            contentType: mimetype,
        });

        await image.save();

        res.status(201).json({ message: 'Image uploaded successfully' });
    } catch (error) {
        console.error('Error uploading image:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
