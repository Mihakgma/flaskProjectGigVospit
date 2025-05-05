$(document).ready(function () {
    $('#inn').on('input', function () { // Используйте id поля inn из вашей формы
        let inn = $(this).val();
        if (inn.length > 0) { // Отправлять запрос, только если поле не пустое
            $.ajax({
                url: '/organizations/check_inn',
                type: 'GET',
                data: {inn: inn},
                success: function (response) {
                    if (response.exists) {
                        $('#inn_warning').text('Организация с таким ИНН уже существует.').show();
                    } else {
                        $('#inn_warning').hide();
                    }
                },
                error: function (error) {
                    console.error("Ошибка при проверке ИНН:", error);
                }
            });
        } else {
            $('#inn_warning').hide(); // Скрыть предупреждение, если поле пустое
        }
    });
});