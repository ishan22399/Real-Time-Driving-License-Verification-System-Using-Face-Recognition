document.addEventListener('DOMContentLoaded', function () {
    const complaintForm = document.getElementById('complaint-form');
    const confirmationMessage = document.getElementById('confirmation');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const body = document.body;

    // Dark Mode Toggle
    darkModeToggle.addEventListener('click', function () {
        body.classList.toggle('dark-mode');
    });

    complaintForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Get form data
        const vehicleMake = document.getElementById('vehicle_make').value;
        const vehicleModel = document.getElementById('vehicle_model').value;
        const licensePlate = document.getElementById('license_plate').value;
        const complaint = document.getElementById('complaint').value;

        // Here, you can send the form data to your server for further processing.
        // For this example, we'll just display a confirmation message.

        // Clear the form fields
        document.getElementById('vehicle_make').value = '';
        document.getElementById('vehicle_model').value = '';
        document.getElementById('license_plate').value = '';
        document.getElementById('complaint').value = '';

        // Display confirmation message
        confirmationMessage.classList.remove('hidden');
    });
});
