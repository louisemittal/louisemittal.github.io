//Centrally located js to prevent tracking my own page visits using exclude_from_tracking cookie set in browser

if (document.cookie.indexOf("exclude_from_tracking=true") === -1) {
    // Load the Google Analytics tracking script asynchronously
    (function() {
        var script = document.createElement('script');
        script.src = 'https://www.googletagmanager.com/gtag/js?id=G-MSYL07FET5';
        script.async = true;
        document.head.appendChild(script);

        script.onload = function() {
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            // Google Analytics config with your GA4 tracking ID
            gtag('config', 'G-MSYL07FET5');
        };
    })();
}