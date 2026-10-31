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

    function filterValues(field, characteristicId) {
        let selectedIsValid = false;
        Array.from(field.options).forEach((option) => {
            const allowedIds = option.dataset.characteristicIds
                ? option.dataset.characteristicIds.split(",")
                : option.dataset.characteristicId
                  ? [option.dataset.characteristicId]
                  : [];
            const matches = !option.value || allowedIds.includes(characteristicId);
            option.hidden = !matches;
            option.disabled = !matches;
            if (option.selected && matches) {
                selectedIsValid = true;
            }
        });
        if (!selectedIsValid) {
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

        const characteristicId = characteristic.value;
        const selectedOption = characteristic.selectedOptions[0];
        const activeField = typeToField[selectedOption?.dataset.valueType];

        ["value_text", "value_reference"].forEach((name) => {
            const input = state.fields[name].input;
            if (input?.tagName === "SELECT") {
                filterValues(input, characteristicId);
            }
        });

        fieldNames.forEach((name) => {
            const { input, cell } = state.fields[name];
            if (input && cell && input.parentElement !== cell) {
                cell.appendChild(input);
            }
        });

        if (activeField && state.fields[activeField].input && state.valueCell) {
            if (clearInactive) {
                fieldNames.forEach((name) => {
                    if (name !== activeField && state.fields[name].input) {
                        clearField(state.fields[name].input);
                    }
                });
            }
            state.valueCell.appendChild(state.fields[activeField].input);
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

    function initializeExistingRows() {
        document.querySelectorAll(".inline-group tr").forEach(initializeRow);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeExistingRows, { once: true });
    } else {
        initializeExistingRows();
    }

    document.addEventListener("formset:added", (event) => initializeRow(event.target));
})();
