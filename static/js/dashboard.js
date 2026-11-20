// static/js/dashboard.js

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar.classList.contains('-translate-x-full')) {
        // Open Sidebar
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        // Trigger reflow to ensure transition applies
        void overlay.offsetWidth; 
        overlay.classList.remove('opacity-0');
    } else {
        // Close Sidebar
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => {
            overlay.classList.add('hidden');
        }, 300); // Wait for transition
    }
}

// Add fade-in animation to main content on load
document.addEventListener('DOMContentLoaded', () => {
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }
});