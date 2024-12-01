document.addEventListener("DOMContentLoaded", function () {
        if (sessionStorage.getItem("OrderComplete") === 'true') {
        const popup = Notification({
            position: 'top-right',
            duration: 4000,
            isHidePrev: false,
            isHideTitle: false,
            maxOpened: 3,
        });

        popup.setProperty({
            duration: 5000,
            isHidePrev: true,
        });

        popup.success({
            title: 'Success!',
            message: "Thank you for your purchase! A confirmation email with your receipt has been sent to your email address. Please check your inbox."
        });

        sessionStorage.removeItem("OrderComplete");
    }
});
