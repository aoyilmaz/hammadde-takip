/**
 * Silo Takip — Frontend JavaScript
 * Sidebar toggle, tarih gösterimi, flash mesaj otomatik kapanma
 */

// Sidebar açma/kapama (mobil)
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// Sayfa dışına tıklayınca sidebar kapat (mobil)
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('menuToggle');
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
    }
});

// Güncel tarih gösterimi
function updateDate() {
    const el = document.getElementById('currentDate');
    if (el) {
        const now = new Date();
        const options = { day: '2-digit', month: '2-digit', year: 'numeric', weekday: 'long' };
        el.textContent = now.toLocaleDateString('tr-TR', options);
    }
}
updateDate();

// Tarih input'larına bugünün tarihini otomatik ata (boşsa)
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input[type="date"]').forEach(function(input) {
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });

    // Flash mesajları 5 saniye sonra otomatik kapat
    setTimeout(function() {
        document.querySelectorAll('.flash-message').forEach(function(msg) {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(function() { msg.remove(); }, 300);
        });
    }, 5000);
});
