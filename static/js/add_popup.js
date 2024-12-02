document.addEventListener("DOMContentLoaded", function () {
    const addToCartButton = document.getElementById("addToCartButton");

    if (addToCartButton) {
        addToCartButton.addEventListener("click", async function (event) {
            event.preventDefault();

            try {
                const productDetails = {
                    product_name: "Sample Product",
                    product_price: 29.99,
                    product_image: "sample.jpg",
                    product_quantity: 1,
                };

                const response = await fetch('/add_to_cart', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(productDetails),
                });

                if (!response.ok) {
                    throw new Error("Server error: " + response.statusText);
                }

                const result = await response.json();

                // Show notification based on the response
                const popup = Notification({
                    position: 'center',
                    duration: 4000,
                    isHidePrev: false,
                    isHideTitle: false,
                    maxOpened: 3,
                });

                if (response.status === 200) {
                    popup.success({
                        title: `<div class="title-cust title-success">Success</div>`,
                        message: `<div class="wrapper-notification">
                            <div class="icons icon-success"></div>
                            <div class="message message-text-success">${result.message}</div></div>`,
                    });
                } else {
                    popup.error({
                        title: `<div class="title-cust title-error">Error</div>`,
                        message: `<div class="wrapper-notification">
                            <div class="icons icon-error"></div>
                            <div class="message message-text-error">${result.message}</div></div>`,
                    });
                }
            } catch (error) {
                console.error("An error occurred:", error);
                alert("An unexpected error occurred. Please try again later.");
            }
        });
    }
});
