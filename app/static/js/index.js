document.addEventListener("DOMContentLoaded", function() {
    const genderSelect = document.getElementById("gender");

    genderSelect.addEventListener('change', () => {
        genderSelect.classList.add('selected-not-disabled');
    });
});
