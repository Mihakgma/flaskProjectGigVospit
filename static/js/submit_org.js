function submitOrganization() {
    const formData = {
        inn: $('#inn').val(),
        name: $('#name').val(),
        email: $('#email').val(),
        is_active: $('#is_active').prop('checked'),
        info: $('#info').val(),
    };

    fetch('/organizations/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData),
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                // Добавьте логику, что делать после успешного добавления
            } else if (data.errors) {
                // Отображение ошибок на странице
                for (const key in data.errors) {
                    $(`#${key}`).next('.alert-danger').text(data.errors[key]);
                }
            } else {
                alert('Произошла неизвестная ошибка.');
            }
        })
        .catch(error => console.error('Ошибка:', error));
}