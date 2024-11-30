document.addEventListener('DOMContentLoaded', function () {
    // Check which page is active based on an element's ID
    const pageType = document.body.dataset.page;

    if (pageType === 'login') {
        document.getElementById('loginForm').addEventListener('submit', function (e) {
            e.preventDefault();
            console.log('Login form submitted');
            // Login logic here
        });
    } else if (pageType === 'register') {
        document.getElementById('registerForm').addEventListener('submit', function (e) {
            e.preventDefault();
            console.log('Register form submitted');
            // Registration logic here
        });
    } else if (pageType === 'forgot-password') {
        document.getElementById('forgotPasswordForm').addEventListener('submit', function (e) {
            e.preventDefault();
            console.log('Forgot password form submitted');
            // Forgot password logic here
        });
    }
});

function showPage(newPageId) {
    const currentPage = document.querySelector('.active-page');
    const newPage = document.getElementById(newPageId);

    if (!newPage || currentPage === newPage) return; // Prevent redundant transitions

    // Start exit animation for the current page
    currentPage.classList.add('page-exit');
    currentPage.classList.remove('active-page');

    // Remove the exit class after the animation ends
    currentPage.addEventListener('transitionend', () => {
        currentPage.classList.remove('page-exit');
    }, { once: true });

    // Start enter animation for the new page
    newPage.classList.add('page-enter');
    setTimeout(() => {
        newPage.classList.remove('page-enter');
        newPage.classList.add('active-page');
    }, 0); // Allow the browser to re-render before applying the class
}