(function () {
    const messageField = document.getElementById("message");
    const continueBtn = document.getElementById("continue-btn");
    const skipBtn = document.getElementById("skip-btn");

    function update() {
        const filled = messageField.value.trim() !== "";
        continueBtn.hidden = !filled;
        skipBtn.hidden = filled;
    }

    messageField.addEventListener("input", update);
    update();
})();
