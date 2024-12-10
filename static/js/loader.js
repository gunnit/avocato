function handleRegenerate(url) {
    var btn = document.querySelector('.regenerate-btn');
    if (btn) {
        btn.classList.add('loading');
    }
    window.location.href = url;
}
