// loader.js
document.addEventListener("DOMContentLoaded", function() {
  const loader = document.querySelector('.loader');
  if (loader) {
    setTimeout(() => {
      loader.style.display = 'none';
    }, 3000); // Simulate a 3-second loading time
  }
});
