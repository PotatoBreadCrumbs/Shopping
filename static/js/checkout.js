document.addEventListener("DOMContentLoaded", function () {
    const proceedButton = document.getElementById("proceedButton");

    // Initialize notification system
    const popup = Notification({
        position: 'center',
        duration: 4000,
        isHidePrev: false,
        isHideTitle: false,
        maxOpened: 3,
    });

    popup.setProperty({
        duration: 7500,
        isHidePrev: true,
    });

    if (proceedButton) {
        proceedButton.addEventListener("click", async function (event) {
            event.preventDefault(); // Prevent default form submission

            try {
                // Collect form data
                const form = document.querySelector("form"); // Select the checkout form
                const formData = new FormData(form);
                const payload = Object.fromEntries(formData.entries()); // Convert FormData to JSON object

                // Send request to process_checkout
                const response = await fetch('/process_checkout', {
                    method: 'POST',
                    body: new FormData(form), // Send FormData directly
                });

                if (!response.ok) {
                    throw new Error("Server returned an error: " + response.statusText);
                }

                const result = await response.json();
                console.log("Backend response:", result); // Debugging in console

                // Handle different responses from the backend
                if (result.message === "MissingFields") {
                    popup.error({
                        title: `<div class="title-cust title-error">Missing Fields</div>`,
                        message: `<div class="wrapper-notification">
                            <div class="icons icon-error"></div>
                            <div class="message message-text-error">The following fields are missing: ${result.errors.join(
                                ", "
                            )}</div></div>`,
                    });
                } 
                 else if (result.message === "OrderComplete") {
                    sessionStorage.setItem("OrderComplete", "true");
                    window.location.href = result.redirect_url; // Redirect on success
                } else if (result.message === "EmailIssue") {
                    popup.error({
                        title: `<div class="title-cust title-warning">Email Issue</div>`,
                        message: `<div class="wrapper-notification">
                            <div class="icons icon-warning"></div>
                            <div class="message message-text-warning">Order placed, but there was an issue sending the confirmation email.</div></div>`,
                    });
                }
            } catch (error) {
                console.error("An error occurred during checkout:", error);

                popup.error({
                    title: `<div class="title-cust title-error">Unexpected Error</div>`,
                    message: `<div class="wrapper-notification">
                        <div class="icons icon-error"></div>
                        <div class="message message-text-error">An unexpected error occurred. Please try again later.</div></div>`,
                });
            }
        });
    }
});
