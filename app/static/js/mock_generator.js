document.addEventListener('DOMContentLoaded', function () {
  const fieldsContainer = document.getElementById('fieldsContainer');
  const addFieldButton = document.getElementById('addFieldButton');
  const clearButton = document.getElementById('clearButton');
  const submitButton = document.getElementById('submitButton');

  // Счётчик полей, чтобы пронумеровать «Поле 1», «Поле 2» и т.д.
  let fieldCount = 1;

  // 1. Сразу при загрузке сохраняем «шаблон» первого поля в памяти,
  //    чтобы потом клонировать даже если никто не будет присутствовать в DOM.
  const fieldTemplate = document.querySelector('.field-section').cloneNode(true);

  // 2. Функция, которая отображает или скрывает div.constraints-… в зависимости от выбранного типа
  function setConstraintsVisibility(selectElement) {
    const fieldSection = selectElement.closest('.accordion-body');
    const selectedType = selectElement.value;

    const constraintsDivs = fieldSection.querySelectorAll('[class^="constraints-"]');
    constraintsDivs.forEach((div) => {
      // Показываем только тот div, чей класс содержит `constraints-<type>`
      div.style.display = div.classList.contains(`constraints-${selectedType}`)
        ? 'block'
        : 'none';
    });
  }

  // 3. Функция, которая назначает ВСЕ обработчики (delete, clear, change-type, change-name)
  //    на конкретный элемент .field-section.
  function attachListenersToFieldSection(section, currentIndex) {
    // 3.a) Слушатель для «Тип поля»
    const selectType = section.querySelector('.field-type-select');
    selectType.addEventListener('change', function () {
      // при смене типа показываем нужные ограничения
      setConstraintsVisibility(this);
    });
    // При инициализации показываем только string-ограничения
    setConstraintsVisibility(selectType);

    // 3.b) Слушатель для «Удалить поле»
    const deleteBtn = section.querySelector('.delete-field');
    deleteBtn.addEventListener('click', function () {
      section.remove();
      // Если после удаления не осталось ни одного секшена,
      // сбрасываем fieldCount так, чтобы следующий add-сгенерировал «Поле 1»
      const remaining = fieldsContainer.querySelectorAll('.field-section').length;
      if (remaining === 0) {
        fieldCount = 0;
      }
    });

    // 3.c) Слушатель для «Очистить» (только внутри этого блока)
    const clearBtn = section.querySelector('.clear-field');
    clearBtn.addEventListener('click', function () {
      // Находим все input и textarea внутри этого .field-section и обнуляем их
      section.querySelectorAll('input, textarea').forEach((el) => {
        // если это селект, сбрасываем на 'string'
        if (el.tagName.toLowerCase() === 'select') {
          el.value = 'string';
        } else {
          el.value = '';
        }
      });
      // После сброса select-а, пересчитываем видимость constraints
      const sel = section.querySelector('.field-type-select');
      setConstraintsVisibility(sel);

      // Заголовок аккордеона тоже обновляется (если поле пустое, покажем «Поле N»)
      const nameInput = section.querySelector('.field-name');
      const headerBtn = section.querySelector('.accordion-button');
      if (nameInput.value.trim() === '') {
        headerBtn.textContent = `Поле ${currentIndex}`;
      }
    });

    // 3.d) Слушатель для «Имя поля» – меняем заголовок аккордеона на тот текст, что ввёл пользователь
    const nameInput = section.querySelector('.field-name');
    const headerBtn = section.querySelector('.accordion-button');
    nameInput.addEventListener('input', function () {
      const val = this.value.trim();
      if (val === '') {
        headerBtn.textContent = `Поле ${currentIndex}`;
      } else {
        headerBtn.textContent = val;
      }
    });
  }

  // 4. Инициализация первого поля (оно уже есть в DOM).
  //    Вешаем на него все слушатели.
  const firstSection = document.querySelector('.field-section');
  attachListenersToFieldSection(firstSection, fieldCount);

  // 5. Обработчик кнопки «Добавить поле»
  addFieldButton.addEventListener('click', function () {
    fieldCount++;

    // Клонируем «шаблон», сохранённый при загрузке
    const newFieldSection = fieldTemplate.cloneNode(true);

    // Очищаем все input/textarea внутри нового клона
    newFieldSection.querySelectorAll('input, textarea').forEach((el) => (el.value = ''));
    // Сбрасываем выбор select-ов внутри клона на значение по умолчанию
    newFieldSection.querySelectorAll('select').forEach((el) => (el.value = 'string'));

    // Переименовываем id/aria-атрибуты аккуратно, чтобы аккордеон работал независимо
    // Генерируем новые уникальные id
    const newAccordionId = `accordionField${fieldCount}`;
    const newHeadingId = `headingField${fieldCount}`;
    const newCollapseId = `collapseField${fieldCount}`;

    // Устанавливаем новый ID для обёртки-аккордеона
    const accordionWrapper = newFieldSection.querySelector('.accordion');
    accordionWrapper.id = newAccordionId;

    // Заголовок
    const accordHeader = newFieldSection.querySelector('.accordion-header');
    accordHeader.id = newHeadingId;
    const accordButton = newFieldSection.querySelector('.accordion-button');
    accordButton.setAttribute('data-bs-target', `#${newCollapseId}`);
    accordButton.setAttribute('aria-controls', newCollapseId);
    accordButton.textContent = `Поле ${fieldCount}`; // по дефолту «Поле N»

    // Контейнер для тела (collapse)
    const accordCollapse = newFieldSection.querySelector('.accordion-collapse');
    accordCollapse.id = newCollapseId;
    accordCollapse.setAttribute('aria-labelledby', newHeadingId);
    accordCollapse.setAttribute('data-bs-parent', `#${newAccordionId}`);

    // Вешаем все слушатели на новый блок
    attachListenersToFieldSection(newFieldSection, fieldCount);

    // Вставляем в контейнер
    fieldsContainer.appendChild(newFieldSection);
  });

  // 6. Обработчик «Очистить всю форму»
  clearButton.addEventListener('click', function () {
    // Очищаем контейнер целиком
    fieldsContainer.innerHTML = '';
    // Сбрасываем счётчик, чтобы следующее поле стало «Поле 1»
    fieldCount = 0;

    // Создаём один пустой блок (с нуля)
    addFieldButton.click();
  });

  // 7. Сбор данных с формы при нажатии «Отправить»
  function collectFieldsData() {
    const fieldSections = fieldsContainer.querySelectorAll('.field-section');
    const fields = [];

    fieldSections.forEach((section) => {
      const fieldName = section.querySelector('.field-name').value.trim() || null;
      const fieldType = section.querySelector('.field-type-select').value;
      const description = section.querySelector('.description').value.trim() || null;
      const constraints = getConstraints(section, fieldType);

      fields.push({ fieldName, fieldType, description, constraints });
    });

    return fields;
  }

  // 8. Функция для получения ограничений в зависимости от типа
  function getConstraints(section, type) {
    const constraintsDiv = section.querySelector(`.constraints-${type}`);
    const constraints = {
      minLength: null,
      maxLength: null,
      minimum: null,
      maximum: null,
      pattern: null,
      enum: null,
      items: null,
      dateFormat: null,
    };

    if (type === 'string') {
      constraints.minLength = constraintsDiv.querySelector('.min-length').value || null;
      constraints.maxLength = constraintsDiv.querySelector('.max-length').value || null;
      constraints.pattern = constraintsDiv.querySelector('.pattern').value || null;
      const enumValue = constraintsDiv.querySelector('.enum').value;
      constraints.enum = enumValue
        ? enumValue.split(',').map((v) => v.trim())
        : null;
    } else if (type === 'number') {
      constraints.minimum = constraintsDiv.querySelector('.minimum').value || null;
      constraints.maximum = constraintsDiv.querySelector('.maximum').value || null;
      const enumValue = constraintsDiv.querySelector('.enum').value;
      constraints.enum = enumValue
        ? enumValue.split(',').map((v) => parseFloat(v.trim()))
        : null;
    } else if (type === 'boolean') {
      // булево не имеет дополнительных настроек
    } else if (type === 'array') {
      const enumValue = constraintsDiv.querySelector('.enum').value;
      constraints.enum = enumValue
        ? enumValue.split(',').map((v) => v.trim())
        : null;

      const itemsType = constraintsDiv.querySelector('.items-type').value;
      const itemsPropsValue = constraintsDiv.querySelector('.items-properties').value;
      constraints.items = {
        type: itemsType,
        properties: itemsPropsValue ? JSON.parse(itemsPropsValue) : null,
      };
    } else if (type === 'date') {
      constraints.minimum = constraintsDiv.querySelector('.minimum').value || null;
      constraints.maximum = constraintsDiv.querySelector('.maximum').value || null;
      constraints.dateFormat = constraintsDiv.querySelector('.date-format').value || null;
    }

    return constraints;
  }

  // 9. При клике «Отправить» собираем данные и выводим в консоль
  submitButton.addEventListener('click', function() {
    const mockCount = document.getElementById('mockCount').value;
    const fields = collectFieldsData();

    if (!fields || fields.length === 0) {
        alert('Пожалуйста, добавьте хотя бы одно поле');
        return;
    }

    const jsonData = { count: parseInt(mockCount, 10), fields: fields };
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    fetch('/mock_generator', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(jsonData),
    })
    .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка сервера');
        }
        
        // Обрабатываем разные форматы ответа
        let mockData;
        if (data.mockData) {
            mockData = data.mockData;
        } else if (data.data) {
            mockData = JSON.stringify(data.data);
        } else {
            throw new Error('Неверный формат ответа от сервера');
        }
        
        const encodedData = encodeURIComponent(mockData);
        window.location.href = `/mock_result?data=${encodedData}`;
    })
    .catch((error) => {
        console.error('Ошибка:', error);
        alert(error.message || 'Произошла ошибка при отправке данных.');
    });
});
});
