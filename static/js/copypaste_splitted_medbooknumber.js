// Обработчик вставки для номера мед. книжки
document.getElementById('medbook_part1').addEventListener('paste', function (e) {
    const pastedData = e.clipboardData.getData('text');
    const parts = pastedData.split('-');
    if (parts.length === 4) {
        document.getElementById('medbook_part1').value = parts[0];
        document.getElementById('medbook_part2').value = parts[1];
        document.getElementById('medbook_part3').value = parts[2];
        document.getElementById('medbook_part4').value = parts[3];
        e.preventDefault();
    }
});