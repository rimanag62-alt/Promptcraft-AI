// PromptCraft AI - Global Scripts

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const CSRF_TOKEN = getCookie('csrftoken');

// Alert dismissals
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 200);
            }
        });
    });

    // Auto-dismiss success messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert-success').forEach(alert => {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        });
    }, 5000);
});
