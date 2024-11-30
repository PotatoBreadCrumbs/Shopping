function isOSDarkMode() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function loadExternalScript(url, callback) {
    const existingScript = document.querySelector(`script[src="${url}"]`);
    if (!existingScript) {
        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        script.onload = callback;
        document.head.appendChild(script);
        console.log(`Script loaded: ${url}`);
    } else {
        console.log(`Script already loaded: ${url}`);
        callback(); // Call callback if already loaded
    }
}

function initializeDarkReader() {
    if (window.DarkReader) {
        console.log('Initializing Dark Reader...');
        DarkReader.setFetchMethod(window.fetch);
        DarkReader.enable({
            brightness: 90,
            contrast: 100,
            sepia: 10,
        });
    } else {
        console.error('DarkReader is not available.');
    }
}

function runScriptIfDarkMode(scriptUrl) {
    if (isOSDarkMode()) {
        loadExternalScript(scriptUrl, initializeDarkReader);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const darkModeScript = 'https://cdn.jsdelivr.net/npm/darkreader/darkreader.min.js';
    runScriptIfDarkMode(darkModeScript);

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
        if (e.matches) {
            console.log('Detected dark mode change.');
            runScriptIfDarkMode(darkModeScript);
        }
    });
});