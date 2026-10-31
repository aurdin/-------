document.addEventListener("formset:added", (event) => {
    const row = event.target;
    const positionInput = row.querySelector('input[name$="-position"]');
    const inlineGroup = row.closest(".inline-group");

    if (!positionInput || !inlineGroup) {
        return;
    }

    let maxPosition = 0;
    inlineGroup.querySelectorAll('input[name$="-position"]').forEach((input) => {
        if (input === positionInput || input.value.trim() === "") {
            return;
        }

        const position = Number.parseInt(input.value, 10);
        if (Number.isInteger(position)) {
            maxPosition = Math.max(maxPosition, position);
        }
    });

    positionInput.value = String(maxPosition + 1);
});
