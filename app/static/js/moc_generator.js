document.addEventListener('DOMContentLoaded', function() {
    const fieldTypeSelect = document.getElementById('fieldTypeSelect');
    const constraintsDivs = {
        string: document.getElementById('stringConstraints'),
        number: document.getElementById('numberConstraints'),
        boolean: document.getElementById('booleanConstraints'),
        array: document.getElementById('arrayConstraints'),
        date: document.getElementById('dateConstraints')
    };

    function updateConstraints() {
        const selectedType = fieldTypeSelect.value;
        for (const type in constraintsDivs) {
            constraintsDivs[type].style.display = (type === selectedType) ? 'block' : 'none';
        }
    }

    fieldTypeSelect.addEventListener('change', updateConstraints);
    updateConstraints();

    document.getElementById('submitButton').addEventListener('click', function() {
        const fieldData = collectFieldData();
        const jsonData = {
            count: 1,
            fields: [fieldData]
        };

        fetch("/moc_generator", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));
    });

    function collectFieldData() {
        const fieldName = document.getElementById('fieldName').value;
        const fieldType = document.getElementById('fieldTypeSelect').value;
        let constraints = {};

        if (fieldType === 'string') {
            constraints = {
                minLength: document.getElementById('minLength').value || null,
                maxLength: document.getElementById('maxLength').value || null,
                minimum: null,
                maximum: null,
                pattern: document.getElementById('pattern').value || null,
                enum: document.getElementById('enumString').value ? document.getElementById('enumString').value.split(',') : null,
                items: null,
                dateFormat: null
            };
        } else if (fieldType === 'number') {
            constraints = {
                minLength: null,
                maxLength: null,
                minimum: document.getElementById('minimumNumber').value || null,
                maximum: document.getElementById('maximumNumber').value || null,
                pattern: null,
                enum: document.getElementById('enumNumber').value ? document.getElementById('enumNumber').value.split(',') : null,
                items: null,
                dateFormat: null
            };
        } else if (fieldType === 'boolean') {
            constraints = {
                minLength: null,
                maxLength: null,
                minimum: null,
                maximum: null,
                pattern: null,
                enum: null,
                items: null,
                dateFormat: null
            };
        } else if (fieldType === 'array') {
            const itemsProperties = document.getElementById('itemsProperties').value;
            constraints = {
                minLength: null,
                maxLength: null,
                minimum: null,
                maximum: null,
                pattern: null,
                enum: document.getElementById('enumArray').value ? document.getElementById('enumArray').value.split(',') : null,
                items: {
                    type: document.getElementById('itemsType').value,
                    properties: itemsProperties ? JSON.parse(itemsProperties) : null
                },
                dateFormat: null
            };
        } else if (fieldType === 'date') {
            constraints = {
                minLength: null,
                maxLength: null,
                minimum: document.getElementById('minimumDate').value || null,
                maximum: document.getElementById('maximumDate').value || null,
                pattern: null,
                enum: null,
                items: null,
                dateFormat: document.getElementById('dateFormat').value || null
            };
        }

        return {
            fieldName: fieldName,
            fieldType: fieldType,
            constraints: constraints,
            description: document.getElementById(`description${fieldType.charAt(0).toUpperCase() + fieldType.slice(1)}`).value || null
        };
    }
});