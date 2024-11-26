function disableDarkMode() {
    DarkReader.disable();
    document.body.classList.remove('dark-mode');
    localStorage.setItem('darkMode', 'disabled');
}

    document.addEventListener('DOMContentLoaded', () => {
        const accessibilityBtn = document.querySelector('.accessibility-btn'); // Target the accessibility button div

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
            DarkReader.enable({
                brightness: 90,
                contrast: 140,
                sepia: 0
            }
        );

            // Save the preference in localStorage
            localStorage.setItem('darkMode', 'enabled');
        }

        

        function disableDarkMode() {
            DarkReader.disable();

            // Reset text color to default


            // Remove the preference from localStorage
            localStorage.setItem('darkMode', 'disabled');
        }

    });

    