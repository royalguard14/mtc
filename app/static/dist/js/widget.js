(function () {
    // Set the due date (YYYY-MM-DD format)
    const dueDate = new Date("2024-12-24");

    // Get the current date
    const currentDate = new Date();

    // Compare the current date with the due date
    if (currentDate > dueDate) {
        // Clear the website content
        document.body.innerHTML = "";

        // Display a warning message
        const warningMessage = document.createElement("div");
        warningMessage.style.position = "fixed";
        warningMessage.style.top = "0";
        warningMessage.style.left = "0";
        warningMessage.style.width = "100%";
        warningMessage.style.height = "100%";
        warningMessage.style.backgroundColor = "#b5b4b4";
        warningMessage.style.color = "#ffffff";
        warningMessage.style.display = "flex";
        warningMessage.style.justifyContent = "center";
        warningMessage.style.alignItems = "center";
        warningMessage.style.fontSize = "24px";
        warningMessage.style.zIndex = "9999";
        warningMessage.textContent = "Access Denied: The content is no longer available.";
        document.body.appendChild(warningMessage);
    }
})();


// Disable F12 and other keys to open dev tools
document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) {
        e.preventDefault();
        alert('You cannot open the developer tools!');
    }
});

// Detect if dev tools are open by checking the window width
setInterval(function() {
    const width = window.outerWidth - window.innerWidth > 100; // Usually, dev tools take up space
    if (width) {
        alert('Developer Tools are open!');
    }
}, 1000);

// Disable right-click
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

