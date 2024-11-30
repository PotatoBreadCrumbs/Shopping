document.getElementById("checkoutForm").addEventListener("submit", function (e) {
    const requiredFields = [
        { id: "name", label: "Name on Card" },
        { id: "card-number", label: "Card Number" },
        { id: "expiry", label: "Expiry Date" },
        { id: "cvv", label: "CVV" },
        { id: "address", label: "Shipping Address" },
        { id: "city", label: "City" },
        { id: "zip", label: "ZIP Code" },
        { id: "email", label: "Email" },
    ];

    const missingFields = requiredFields
        .filter(field => !document.getElementById(field.id).value.trim())
        .map(field => field.label);

    if (missingFields.length > 0) {
        e.preventDefault(); // Prevent form submission

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

        popup.error({
            title: `<div class="title-cust title-error">Missing Fields</div>`,
            message: `<div class="wrapper-notification">
                        <div class="icons icon-error"></div>
                        <div class="message message-text-error">
                            The following fields are missing: 
                            <ul>${missingFields.map(field => `<li>${field}</li>`).join("")}</ul>
                        </div>
                      </div>`,
        });
    }
});
