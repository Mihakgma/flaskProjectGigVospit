document.addEventListener('DOMContentLoaded', function () {
    const innInput = document.getElementById('inn_input');
    const checkInnButton = document.getElementById('check_inn_button');
    const innStatusMessage = document.getElementById('inn_status_message');

    if (checkInnButton && innInput && innStatusMessage) {
        checkInnButton.addEventListener('click', function () {
            const inn = innInput.value.trim();
            innStatusMessage.textContent = ''; // Очищаем предыдущее сообщение

            if (!inn) {
                innStatusMessage.textContent = 'Введите ИНН для проверки.';
                innStatusMessage.style.color = 'orange';
                return;
            }

            // Предварительная клиентская валидация формата ИНН
            if (!/^\d{10,12}$/.test(inn)) {
                innStatusMessage.textContent = 'ИНН должен содержать от 10 до 12 цифр и только цифры.';
                innStatusMessage.style.color = 'red';
                return;
            }

            // Отправляем AJAX-запрос на сервер
            fetch(`/organizations/check_inn_exists?inn=${encodeURIComponent(inn)}`)
                .then(response => {
                    // Проверяем статус ответа
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(err.error || 'Ошибка сети');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.exists) {
                        innStatusMessage.textContent = data.message;
                        innStatusMessage.style.color = 'red';
                    } else {
                        innStatusMessage.textContent = data.message;
                        innStatusMessage.style.color = 'green';
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке ИНН:', error);
                    innStatusMessage.textContent = 'Произошла ошибка при проверке ИНН.';
                    innStatusMessage.style.color = 'red';
                });
        });

        // Очищаем сообщение о статусе при изменении поля ИНН
        innInput.addEventListener('input', function () {
            innStatusMessage.textContent = '';
            innStatusMessage.style.color = ''; // Сбросить цвет
        });
    }
});
