(() => {
    const fieldNames = [
        "value_text",
        "value_number",
        "value_boolean",
        "value_reference",
    ];
    const typeToField = {
        text: "value_text",
        number: "value_number",
        boolean: "value_boolean",
        reference: "value_reference",
    };
    const rows = new WeakMap();

    function getField(row, fieldName) {
        return row.querySelector(
            `input[name$="-${fieldName}"], select[name$="-${fieldName}"], textarea[name$="-${fieldName}"]`
        );
    }

    function clearField(field) {
        if (field.type === "checkbox") {
            field.checked = false;
        } else {
            field.value = "";
        }
    }

    function filterCharacteristicValues(field, characteristicId) {
        let selectedValueIsValid = false;
        Array.from(field.options).forEach((option) => {
            const allowedCharacteristicIds = option.dataset.characteristicIds
                ? option.dataset.characteristicIds.split(",")
                : option.dataset.characteristicId
                  ? [option.dataset.characteristicId]
                  : [];
            const matches = !option.value || allowedCharacteristicIds.includes(characteristicId);
            option.hidden = !matches;
            option.disabled = !matches;
            if (option.selected && matches) {
                selectedValueIsValid = true;
            }
        });
        if (!selectedValueIsValid) {
            field.value = "";
        }
    }

    function updateRow(row, clearInactive = false) {
        const characteristic = getField(row, "characteristic");
        if (!characteristic) {
            return;
        }

        let state = rows.get(row);
        if (!state) {
            const fields = Object.fromEntries(
                fieldNames.map((name) => {
                    const input = getField(row, name);
                    return [name, { input, cell: input?.closest("td") }];
                })
            );
            state = { fields, valueCell: fields.value_text.cell };
            rows.set(row, state);
        }

        const selectedOption = characteristic.selectedOptions[0];
        const valueType = selectedOption?.dataset.valueType;
        const activeField = typeToField[valueType];
        const characteristicId = characteristic.value;

        const referenceField = state.fields.value_reference.input;
        if (referenceField) {
            filterCharacteristicValues(referenceField, characteristicId);
        }
        const textField = state.fields.value_text.input;
        if (textField?.tagName === "SELECT") {
            filterCharacteristicValues(textField, characteristicId);
        }

        fieldNames.forEach((name) => {
            const { input, cell } = state.fields[name];
            if (!input || !cell) {
                return;
            }
            if (input.parentElement !== cell) {
                cell.appendChild(input);
            }
        });

        if (activeField && state.fields[activeField].input && state.valueCell) {
            const activeInput = state.fields[activeField].input;
            if (clearInactive) {
                fieldNames.forEach((name) => {
                    if (name !== activeField && state.fields[name].input) {
                        clearField(state.fields[name].input);
                    }
                });
            }
            state.valueCell.appendChild(activeInput);
        }

        fieldNames.forEach((name) => {
            const cell = state.fields[name].cell;
            if (cell) {
                cell.hidden = !activeField || cell !== state.valueCell;
            }
        });

        const table = row.closest("table");
        if (table) {
            ["value_number", "value_boolean", "value_reference"].forEach((name) => {
                const heading = table.querySelector(`th.column-${name}`);
                if (heading) {
                    heading.hidden = true;
                }
            });
        }
    }

    function initializeRow(row) {
        updateRow(row);
        const characteristic = getField(row, "characteristic");
        if (characteristic && !characteristic.dataset.valueHandlerBound) {
            characteristic.dataset.valueHandlerBound = "true";
            characteristic.addEventListener("change", () => updateRow(row, true));
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".inline-group tr").forEach(initializeRow);
    });

    document.addEventListener("formset:added", (event) => {
        initializeRow(event.target);
    });
})();
