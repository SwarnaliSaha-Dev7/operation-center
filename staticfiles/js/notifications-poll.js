/**
 * Refresh unread notification badge periodically (sidebar #notification-nav-badge).
 */
(function () {
  var badge = document.getElementById('notification-nav-badge');
  if (!badge) return;

  var url = '/notification/api/count/';
  function poll() {
    fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var n = parseInt(data.unread, 10) || 0;
        if (n > 0) {
          badge.textContent = n > 99 ? '99+' : String(n);
          badge.classList.remove('hidden');
        } else {
          badge.textContent = '0';
          badge.classList.add('hidden');
        }
      })
      .catch(function () {});
  }

  setInterval(poll, 120000);
})();
