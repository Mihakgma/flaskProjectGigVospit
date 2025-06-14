function setDirectory(inputId) {
    const inputElement = document.getElementById(inputId);
    const fileInput = document.querySelector(`input[name="${inputId}"][type="file"]`);

    if (fileInput.files.length > 0) {
        const filePath = fileInput.files[0].webkitRelativePath; // Получаем относительный путь
        if (filePath) {
            const directoryPath = filePath.split('/')[0];
            inputElement.value = directoryPath;
        } else {
            inputElement.value = ""; // Очищаем, если что-то пошло не так
            console.error("Ошибка: не удалось получить относительный путь.");
            // Можно добавить более подробное сообщение об ошибке пользователю
        }

    } else {
        inputElement.value = ''; // Clear the input if no directory is selected
    }
}