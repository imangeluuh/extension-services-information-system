// Function to disable form fields and submit button
function disableForm(disable) {
    const formFields = ['email', 'password'];
    formFields.forEach(field => {
        document.getElementById(field).disabled = disable;
        document.getElementById(field).value = "";
    });

    document.getElementById('submit').disabled = disable;
}

// Function to start the countdown
function startCountdown() {
    let countdownTime = localStorage.getItem('countdownTime');
    let countdownDisplay = document.getElementById('countdownDisplay'); // Reference to the countdown display span

    countdownDisplay.textContent =  '15 minutes '; // Display initial countdown time

    const countdownInterval = setInterval(() => {
        countdownTime -= 1; // Decrement countdown
        localStorage.setItem('countdownTime', countdownTime);
        if (countdownTime <= 0) {
            clearInterval(countdownInterval); // Stop the countdown when it reaches 0
            localStorage.setItem('entry', 3); // Reset attempts in localStorage
            localStorage.setItem('countdownTime', 900); // Reset countdown time in localStorage
            countdownDisplay.textContent = ''; // Clear countdown display
            document.getElementById('manyAttempt').style.display = 'none'; // Hide the attempt message
            disableForm(false); // Enable form fields and submit button after countdown
        } else {
            if (countdownTime > 60) {
                countdownDisplay.textContent = parseInt(countdownTime / 60) + ' minutes '; // Update countdown text
            } else {
                countdownDisplay.textContent = countdownTime + ' seconds '; // Update countdown text
            }
        }
    }, 1000); // Update every 1 second (1000 milliseconds)
}

// Check entry count on page load and initiate countdown if entry is zero
document.addEventListener("DOMContentLoaded", function(event) {
    if (localStorage.getItem('countdownTime') == null) {
        localStorage.setItem('countdownTime', 900);
    } 

    if (localStorage.getItem('entry') == null) {
        localStorage.setItem('entry', 3);
    }
    if (localStorage.getItem('countdownTime') < 900 || localStorage.getItem('entry') <= 0)  {
        disableForm(true); // Disable form fields and submit button
        document.getElementById('manyAttempt').style.display = 'inline-block'; // Show the attempt message
        startCountdown(); // Start the countdown
    }
});

document.getElementById('loginForm').addEventListener('submit', function(event) {
    let entry = localStorage.getItem('entry') || 3; // Get the stored entry count or set to 3 initially
    let countdownDisplay = document.getElementById('countdownDisplay'); // Reference to the countdown display span

    if (entry <= 0) {
        event.preventDefault(); // Prevent form submission
        disableForm(true); // Disable form fields and submit button
        document.getElementById('manyAttempt').style.display = 'inline-block'; // Show the attempt message
        startCountdown(); // Start the countdown
    } else {
        entry -= 1; // Decrement attempts
        localStorage.setItem('entry', entry); // Update attempts in localStorage
    }
});