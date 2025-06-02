document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM полностью загружен');

    try {
        // Получаем значение переменной из шаблона Flask
        let timeoutValue = "{{ timeout }}";

        const editTimeoutSeconds = parseInt(timeoutValue) || 0;

        console.log('Получено значение таймаута:', editTimeoutSeconds);

        if (editTimeoutSeconds > 0) {
            const timeoutMilliseconds = editTimeoutSeconds * 1000;
            console.log(`Установлен таймаут ${timeoutMilliseconds} мс`);

            setTimeout(function () {
                console.log('Выполняется перенаправление...');
                window.location.href = '/';
            }, timeoutMilliseconds);
        } else {
            console.warn('Таймаут не установлен — нулевое или некорректное значение');
        }
    } catch (error) {
        console.error('Ошибка в скрипте:', error);
    }
});