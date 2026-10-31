document.addEventListener("DOMContentLoaded", () => {
    const classification = document.querySelector("fieldset.product-classification");
    const characteristicsFieldset = document.querySelector(
        ".inline-group fieldset.product-characteristics"
    );
    const characteristics = characteristicsFieldset?.closest(".inline-group");
    const photos = document.querySelector("fieldset.product-photos");
    const details = document.querySelector("fieldset.product-details");

    if (!classification || !characteristics || !photos || !details) {
        return;
    }

    classification.after(characteristics, photos, details);
});
