// loader.js
document.addEventListener("DOMContentLoaded", function() {
  const loader = document.querySelector('.loader');
  if (loader) {
    setTimeout(() => {
      loader.style.display = 'none';
    }, 3000); // Simulate a 3-second loading time
  }
});

// Handle regenerate analysis button click
function handleRegenerate(url) {
  // Find the button that was clicked
  const button = document.querySelector('.regenerate-btn');
  if (button) {
    // Add loading state
    button.classList.add('loading');
    const originalText = button.innerHTML;
    button.innerHTML = `
      <span class="symbol symbol-25px me-3">
        <i class="ki-duotone ki-arrows-circle fs-1">
          <span class="path1"></span>
          <span class="path2"></span>
        </i>
      </span>
      <span class="d-flex flex-column align-items-start">
        <span class="fs-5 fw-bolder">Rigenerando...</span>
        <span class="fs-7">Attendere prego</span>
      </span>
    `;
    button.disabled = true;
  }
  
  // Navigate to the regenerate URL
  window.location.href = url;
}
