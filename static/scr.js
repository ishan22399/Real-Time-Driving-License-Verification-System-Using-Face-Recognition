const body = document.querySelector("body"),
      modeToggle = body.querySelector(".mode-toggle");
      sidebar = body.querySelector("nav");
      sidebarToggle = body.querySelector(".sidebar-toggle");

let getMode = localStorage.getItem("mode");
if(getMode && getMode ==="dark"){
    body.classList.toggle("dark");
}

let getStatus = localStorage.getItem("status");
if(getStatus && getStatus ==="close"){
    sidebar.classList.toggle("close");
}

modeToggle.addEventListener("click", () =>{
    body.classList.toggle("dark");
    if(body.classList.contains("dark")){
        localStorage.setItem("mode", "dark");
    }else{
        localStorage.setItem("mode", "light");
    }
});

// Get references to the input and img elements
const imageUploadInput = document.getElementById("imageUploadInput");
const uploadedImage = document.getElementById("uploadedImage");

// Add an event listener to the input element to handle image selection
imageUploadInput.addEventListener("change", function () {
    const file = this.files[0];
    if (file) {
        // Create a FileReader to read the selected image file
        const reader = new FileReader();

        // Set up a function to run when the image is loaded
        reader.onload = function (e) {
            // Set the img element's source to the selected image
            uploadedImage.src = e.target.result;
        };

        // Read the image file as a data URL
        reader.readAsDataURL(file);
    }
});

sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("close");
    if(sidebar.classList.contains("close")){
        localStorage.setItem("status", "close");
    }else{
        localStorage.setItem("status", "open");
    }
})