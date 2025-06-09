function resetForm() {
    document.getElementById("search_form").reset();

    for (let i = 1; i <= 4; i++) {
        document.getElementById('snils_part' + i).value = '';
        document.getElementById('medbook_part' + i).value = '';
    }
    document.getElementById('last_name').value = '';
    document.getElementById('last_name_exact').value = '';
    document.getElementById('birth_date_start').value = '';
    document.getElementById('birth_date_end').value = '';
    document.getElementById('last_visit_start').value = '';
    document.getElementById('last_visit_end').value = '';
    document.getElementById('registration_address').value = '';
    document.getElementById('residence_address').value = '';
    document.getElementById('updated_by_user').value = 'Все';
    document.getElementById('updated_at_start').value = '';
    document.getElementById('updated_at_end').value = '';
}