// This minimal JavaScript handles form submission without page reload
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            const button = form.querySelector('button');
            const originalText = button.textContent;
            button.textContent = 'Analyzing...';
            button.disabled = true;
            
            // Submit form via Fetch API
            fetch('/', {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                // Replace the content with the new HTML
                document.querySelector('.container').innerHTML = 
                    new DOMParser().parseFromString(html, 'text/html')
                    .querySelector('.container').innerHTML;
            })
            .catch(error => {
                console.error('Error:', error);
                button.textContent = originalText;
                button.disabled = false;
            });
        });
    }
});
