(function () {
    const btn = document.getElementById("copy-btn");
    const urlInput = document.getElementById("link-url");
    if (!btn || !urlInput) return;

    function copy() {
        const text = urlInput.value;
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(onCopied).catch(fallback);
        } else {
            fallback();
        }
    }

    function fallback() {
        urlInput.select();
        urlInput.setSelectionRange(0, 99999);
        var ok = false;
        try {
            ok = document.execCommand("copy");
        } catch (_) {}
        if (ok) {
            onCopied();
        } else {
            window.toast("Couldn't copy the link. Copy it from the field instead.", {
                type: "danger"
            });
        }
    }

    function onCopied() {
        window.toast("Link copied.", {
            type: "success"
        });
    }

    btn.addEventListener("click", copy);
})();
