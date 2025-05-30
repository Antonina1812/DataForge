let fieldIndex = 0;

function addField() {
    const container = document.getElementById('fieldsContainer');
    const fieldDiv = document.createElement('div');
    fieldDiv.classList.add('field');
    fieldDiv.innerHTML = `
        <div class="form-group">
            <label for="fieldName_${fieldIndex}">Имя поля</label>
            <input type="text" id="fieldName_${fieldIndex}" name="fields[${fieldIndex}][fieldName]" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="fieldType_${fieldIndex}">Тип поля</label>
            <select id="fieldType_${fieldIndex}" name="fields[${fieldIndex}][fieldType]" class="form-control" required>
                <option value="string">string</option>
                <option value="number">number</option>
                <option value="boolean">boolean</option>
                <option value="object">object</option>
                <option value="array">array</option>
                <option value="date">date</option>
            </select>
        </div>
        <div class="form-group">
            <label for="description_${fieldIndex}">Описание</label>
            <input type="text" id="description_${fieldIndex}" name="fields[${fieldIndex}][description]" class="form-control">
        </div>
        <button type="button" class="btn btn-danger" onclick="removeField(this)">Удалить поле</button>
        <hr>
    `;
    container.appendChild(fieldDiv);
    fieldIndex++;
}

function removeField(button) {
    button.parentElement.remove();
}

document.getElementById('mockForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const json = Object.fromEntries(formData.entries());
    json.fields = Array.from(document.querySelectorAll('.field')).map(field => {
        const fieldName = field.querySelector('[name$="[fieldName]"]').value;
        const fieldType = field.querySelector('[name$="[fieldType]"]').value;
        const description = field.querySelector('[name$="[description]"]').value;
        return { fieldName, fieldType, description };
    });

    const response = await fetch("/moc_generator", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(json),
    });

    if (response.ok) {
        const result = await response.json();
        alert('Mock объекты успешно сгенерированы!');
        console.log(result);
    } else {
        alert('Ошибка при генерации Mock объектов.');
    }
});
