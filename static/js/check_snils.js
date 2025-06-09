function checkSnilsNumber() {
    let snilsNumber = document.getElementById("form-snils_number").value;
    snilsNumber = snilsNumber.replace(/\D/g, ''); // Удаляем все, кроме цифр

    if (snilsNumber.length !== 11) { // Валидация длины (пример)
        document.getElementById("snils-check-result").innerHTML = "СНИЛС должен содержать 11 цифр.";
        return;
    }

    fetch(`/applicants/check_snils?snils_number=${snilsNumber}`)
        .then(response => response.text())
        .then(data => {
            document.getElementById("snils-check-result").innerHTML = data;
        });
}