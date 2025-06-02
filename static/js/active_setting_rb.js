$(document).ready(function () {
    // Обработчик изменения радиобаттона для активации настройки
    $('input[name="active_setting"]').change(function () {
        const settingId = $(this).val(); // Получаем ID выбранной настройки
        const previousActiveSettingId = "{{ active_setting_id }}"; // Сохраняем ID ранее активной настройки
        const $currentRadio = $(this); // Ссылка на текущий радиобаттон

        $.ajax({
            url: "{{ url_for('settings.activate_setting', setting_id=0) }}".replace('/0', '/' + settingId),
            type: 'POST',
            success: function (response) {
                if (response.status === 'success') {
                    // Если успешно, ничего не делаем, радиобаттон уже выбран
                    console.log(response.message);
                    // Flash-сообщения будут отображены после перезагрузки страницы
                    window.location.reload();
                } else {
                    // Если ошибка, возвращаем радиобаттон к предыдущему состоянию
                    // или перезагружаем страницу, чтобы отразить истинное состояние из БД.
                    console.error('Ошибка активации:', response.message);
                    alert('Не удалось активировать настройку: ' + response.message + '\nСтраница будет перезагружена.');
                    window.location.reload(); // Перезагружаем страницу для синхронизации
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("AJAX Error:", textStatus, errorThrown, jqXHR.responseText);
                alert('Произошла ошибка при активации настройки. Страница будет перезагружена.');
                window.location.reload(); // Перезагружаем страницу
            }
        });
    });
});