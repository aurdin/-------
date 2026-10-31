(() => {
    const boundCharacteristics = new WeakSet();

    function getSelect(row, fieldName) {
        return row.querySelector(`select[name$="-${fieldName}"]`);
    }

    function updateRow(row, characteristicChanged = false) {
        const characteristic = getSelect(row, "characteristic");
        const value = getSelect(row, "value");
        const unit = getSelect(row, "unit");
        if (!characteristic || !value) {
            return;
        }

        const characteristicId = characteristic.value;
        let selectedValueIsValid = false;
        Array.from(value.options).forEach((option) => {
            const matches =
                !option.value || option.dataset.characteristicId === characteristicId;
            option.hidden = !matches;
            option.disabled = !matches;
            if (option.selected && matches) {
                selectedValueIsValid = true;
            }
        });

        if (!selectedValueIsValid || characteristicChanged) {
            value.value = "";
        }

        if (unit && characteristicChanged) {
            unit.value = characteristic.selectedOptions[0]?.dataset.unitId || "";
        }
    }

    function initializeRow(row) {
        const characteristic = getSelect(row, "characteristic");
        if (!characteristic) {
            return;
        }
        updateRow(row);
        if (!boundCharacteristics.has(characteristic)) {
            boundCharacteristics.add(characteristic);
            characteristic.addEventListener("change", () => updateRow(row, true));
        }
    }

    function initializeExistingRows() {
        document.querySelectorAll(".product-characteristics tr").forEach(initializeRow);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeExistingRows, { once: true });
    } else {
        initializeExistingRows();
    }

    document.addEventListener("formset:added", (event) => initializeRow(event.target));
})();
