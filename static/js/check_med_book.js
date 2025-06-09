function checkMedbookNumber() {
    let medbookNumber = document.getElementById("form-medbook_number").value;
    medbookNumber = medbookNumber.replace(/\D/g, ''); // Удаляем все, кроме цифр

    if (medbookNumber.length !== 12) { // Валидация длины (пример)
        document.getElementById("medbook-check-result").innerHTML = "Номер медкнижки должен содержать 12 цифр.";
        return;
    }

    fetch(`/applicants/check_medbook?medbook_number=${medbookNumber}`)
        .then(response => response.text())
        .then(data => {
            document.getElementById("medbook-check-result").innerHTML = data;
        });
}