function disableDarkMode() {
    DarkReader.disable();
    localStorage.setItem('darkMode', 'disabled');
}

document.addEventListener('DOMContentLoaded', () => {
    const accessibilityBtn = document.querySelector('.accessibility-btn'); // Target the accessibility button div
    const bottomNav = document.getElementById("bottomNav"); // Get bottom navigation element

    // Check localStorage for dark mode preference
    const isDarkModeEnabled = localStorage.getItem('darkMode') === 'enabled';

    // Apply dark mode if previously enabled
    if (isDarkModeEnabled) {
        enableDarkMode();
    }

    // Add click event listener to the accessibility button
    accessibilityBtn.addEventListener('click', () => {
        if (DarkReader.isEnabled()) {   
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });

    function enableDarkMode() {
        DarkReader.setFetchMethod(window.fetch);
        DarkReader.enable({
            brightness: 90,
            contrast: 100,
            sepia: 0
        });

        // Apply dark mode to bottom-nav
        document.body.classList.add('dark-mode');
        bottomNav.classList.add('dark-mode');

        // Save the preference in localStorage
        localStorage.setItem('darkMode', 'enabled');
    }

    function disableDarkMode() {
        DarkReader.disable();
        
        // Remove the 'dark-mode' class from body and bottom-nav to revert to default styles
        document.body.classList.remove('dark-mode');
        bottomNav.classList.remove('dark-mode');
        
        // Save the preference in localStorage
        localStorage.setItem('darkMode', 'disabled');
    }
});


    