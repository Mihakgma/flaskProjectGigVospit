document.addEventListener('DOMContentLoaded', function () {
    // Убедитесь, что эти элементы найдены. Проверьте их ID в HTML.
    const editModalElement = document.getElementById('editOrgModal');
    if (!editModalElement) {
        console.error('Модальное окно с ID "editOrgModal" не найдено!');
        return; // Остановить выполнение скрипта, если модальное окно не найдено
    }
    const editModal = new bootstrap.Modal(editModalElement);

    const editOrgForm = document.getElementById('editOrgForm');
    if (!editOrgForm) {
        console.error('Форма с ID "editOrgForm" не найдена!');
        return; // Остановить выполнение скрипта, если форма не найдена
    }

    const orgIdToEditInput = document.getElementById('org_id_to_edit');
    if (!orgIdToEditInput) {
        console.error('Скрытое поле с ID "org_id_to_edit" не найдено!');
        // Продолжаем, так как поле может быть необязательным для открытия модального окна, но понадобится для сохранения
    }

    const saveOrgBtn = document.getElementById('saveOrgBtn');
    const editMessageDiv = document.getElementById('edit-message'); // Убедитесь, что этот div существует

    // Функция для очистки предыдущих ошибок валидации
    function clearValidationErrors() {
        // Проверяем наличие editOrgForm перед использованием
        if (editOrgForm) {
            editOrgForm.querySelectorAll('.is-invalid').forEach(el => {
                el.classList.remove('is-invalid');
            });
            editOrgForm.querySelectorAll('.invalid-feedback').forEach(el => {
                el.textContent = '';
                el.style.display = 'none';
            });
        }
        // Проверяем наличие editMessageDiv перед использованием
        if (editMessageDiv) {
            editMessageDiv.style.display = 'none';
            editMessageDiv.className = 'mt-3'; // Сбросить классы (например, alert-danger/success)
            editMessageDiv.textContent = '';
        }
    }

    // Обработчик нажатия на кнопку "Редактировать" в таблице
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function () {
            console.log('Edit button clicked');
            clearValidationErrors(); // Очищаем ошибки перед открытием
            const orgId = this.getAttribute('data-id');

            // Проверяем наличие orgIdToEditInput перед использованием
            if (orgIdToEditInput) {
                orgIdToEditInput.value = orgId; // Сохраняем ID в скрытом поле
            }


            // Загружаем данные организации по ID через AJAX
            // ИСПРАВЛЕНО: Используем обратные кавычки для шаблонной строки
            fetch(`/api/organizations/${orgId}`)
                .then(response => {
                    if (!response.ok) {
                        // В случае HTTP ошибки (404, 500 и т.д.)
                        // Пробуем получить текст ошибки из ответа, если доступен
                        return response.text().then(text => {
                            console.error('HTTP error!', response.status, text);
                            throw new Error(`Ошибка загрузки данных организации: ${response.status} ${response.statusText}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // Проверяем наличие полей формы перед заполнением
                    const nameInput = document.getElementById('name');
                    const innInput = document.getElementById('inn');
                    const addressInput = document.getElementById('address');
                    const phoneNumberInput = document.getElementById('phone_number');
                    const emailInput = document.getElementById('email');
                    const isActiveCheckbox = document.getElementById('is_active'); // Убедитесь, что это ID чекбокса
                    const infoInput = document.getElementById('info');

                    if (nameInput) nameInput.value = data.name;
                    if (innInput) innInput.value = data.inn;
                    // ИСПРАВЛЕНО: Используем оператор нулевого слияния ??
                    if (addressInput) addressInput.value = data.address ?? '';
                    if (phoneNumberInput) phoneNumberInput.value = data.phone_number ?? '';
                    if (emailInput) emailInput.value = data.email ?? '';
                    if (isActiveCheckbox) isActiveCheckbox.checked = data.is_active;
                    if (infoInput) infoInput.value = data.info ?? '';


                    // Открываем модальное окно
                    // Проверяем, что модальный объект успешно создан
                    if (editModal) {
                        editModal.show();
                    } else {
                        console.error("Объект Bootstrap Modal не инициализирован.");
                    }

                })
                .catch(error => {
                    console.error('Error loading organization data:', error);
                    alert('Не удалось загрузить данные организации: ' + error.message); // Показываем сообщение об ошибке
                });
        });
    });

    // Обработчик нажатия на кнопку "Сохранить изменения" в модальном окне
    // Проверяем наличие saveOrgBtn перед добавлением обработчика
    if (saveOrgBtn) {
        saveOrgBtn.addEventListener('click', function (event) {
            event.preventDefault(); // Предотвращаем стандартную отправку формы
            clearValidationErrors(); // Очищаем ошибки перед отправкой

            const orgId = orgIdToEditInput.value;
            const formData = new FormData(editOrgForm); // Собираем данные формы

            // Convert FormData to JSON object
            const jsonData = {};
            formData.forEach((value, key) => {
                // Handle boolean for checkbox
                if (key === 'is_active') {
                    jsonData[key] = value === 'on'; // Checkboxes submit 'on' when checked
                } else {
                    jsonData[key] = value;
                }
            });

            // Отправляем данные на сервер через AJAX (PUT запрос)
            fetch(`/api/organizations/${orgId}`, {
                method: 'PUT', // Используем PUT для обновления
                headers: {
                    'Content-Type': 'application/json',
                    // Возможно, потребуется CSRF-токен, если вы его используете
                    // 'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(jsonData)
            })
                .then(response => {
                    // Пытаемся обработать как JSON, но учитываем, что ответ может быть пустым
                    const contentType = response.headers.get("content-type");
                    if (!response.ok) {
                        if (contentType && contentType.indexOf("application/json") !== -1) {
                            return response.json().then(data => {
                                // Если сервер вернул JSON с ошибками валидации
                                console.error('Validation Error Response:', data);
                                if (data.errors) {
                                    displayValidationErrors(data.errors); // Функция для отображения ошибок
                                } else {
                                    // Другая ошибка сервера, но с JSON ответом
                                    displayMessage('Произошла ошибка при сохранении: ' + (data.message || response.statusText), 'alert-danger');
                                }
                                throw new Error('Validation or Server Error'); // Пробрасываем ошибку дальше
                            });
                        } else {
                            // Сервер вернул не-JSON ответ при ошибке (например, 500 Internal Server Error page)
                            return response.text().then(text => {
                                console.error('Server Error Response:', response.status, text);
                                displayMessage(`Ошибка сервера: ${response.status} ${response.statusText}`, 'alert-danger');
                                throw new Error('Server Error'); // Пробрасываем ошибку дальше
                            });
                        }
                    } else {
                        // Успешный ответ (200 OK, 204 No Content)
                        if (contentType && contentType.indexOf("application/json") !== -1) {
                            // Успех с JSON ответом (может содержать обновленные данные)
                            return response.json();
                        } else {
                            // Успех без JSON ответа (например, 204 No Content)
                            return {}; // Возвращаем пустой объект, чтобы следующий .then не упал
                        }
                    }
                })
                .then(data => {
                    // Этот блок выполняется только при успешном ответе (response.ok is true)
                    console.log('Организация успешно обновлена:', data);
                    displayMessage('Изменения сохранены успешно!', 'alert-success');

                    // Опционально: Закрыть модальное окно и/или обновить список организаций
                    // editModal.hide(); // Закрыть модальное окно
                    // location.reload(); // Перезагрузить страницу для отображения изменений
                    // Или обновить только нужную строку в таблице без перезагрузки
                })
                .catch(error => {
                    console.error('Error saving organization data:', error);
                    // Ошибки, которые уже были обработаны и показаны через displayMessage, здесь не требуют alert
                    if (!error.message.startsWith('Ошибка загрузки данных') && !error.message.startsWith('Validation or Server Error') && !error.message.startsWith('Server Error')) {
                        // Показываем alert только для необработанных ошибок fetch
                        alert('Не удалось сохранить изменения организации: ' + error);
                    }
                });
        });
    } else {
        console.error('Кнопка с ID "saveOrgBtn" не найдена!');
    }


    // Вспомогательная функция для отображения ошибок валидации
    function displayValidationErrors(errors) {
        clearValidationErrors(); // Очистить предыдущие
        for (const fieldName in errors) {
            const inputElement = document.getElementById(fieldName);
            if (inputElement) {
                inputElement.classList.add('is-invalid');
                // Находим следующий элемент с классом invalid-feedback или создаем его
                let feedbackElement = inputElement.nextElementSibling;
                if (!feedbackElement || !feedbackElement.classList.contains('invalid-feedback')) {
                    feedbackElement = document.createElement('div');
                    feedbackElement.classList.add('invalid-feedback');
                    inputElement.parentNode.insertBefore(feedbackElement, inputElement.nextSibling);
                }
                feedbackElement.textContent = errors[fieldName].join(' '); // Объединяем все ошибки для поля
                feedbackElement.style.display = 'block';
            } else {
                console.warn(`Элемент формы для поля "${fieldName}" не найден.`);
                // Если нет поля, можно показать ошибку в общем блоке
                displayMessage(`Ошибка для поля ${fieldName}: ${errors[fieldName].join(' ')}`, 'alert-danger');
            }
        }
        // Если есть ошибки валидации, прокрутить к первой форме с ошибкой или к сообщению
        const firstInvalid = editOrgForm.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.scrollIntoView({behavior: 'smooth', block: 'center'});
        } else if (editMessageDiv && editMessageDiv.style.display === 'block') {
            editMessageDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
        }
    }

    // Вспомогательная функция для отображения общих сообщений
    function displayMessage(message, type) { // type может быть 'alert-success', 'alert-danger'
        if (editMessageDiv) {
            editMessageDiv.textContent = message;
            editMessageDiv.className = `mt-3 alert ${type}`;
            editMessageDiv.style.display = 'block';
            // Прокрутить к сообщению
            editMessageDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
        } else {
            // Если нет элемента для сообщения, использовать alert
            alert(message);
        }
    }

});
