$(document).ready(function() {
    $('#organization_select').select2({
        ajax: {
            url: '/organizations/search',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term, // term - введенный текст для поиска
                    page: params.page
                };
            }, // <-- Добавлена закрывающая скобка и запятая
            processResults: function (data, params) {
                params.page = params.page || 1;
                return {
                    results: data.items,
                    pagination: {
                        more: (params.page * 30) < data.total_count
                    }
                };
            },
            cache: true
        },
        placeholder: 'Выберите организацию',
        minimumInputLength: 3
    });
});
