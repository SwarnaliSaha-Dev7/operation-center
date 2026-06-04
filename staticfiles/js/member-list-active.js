/**
 * Member list: toggle is_active via POST (Active column checkboxes).
 */
(function () {
  'use strict';

  function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  document.body.addEventListener('change', function (e) {
    var input = e.target;
    if (!input || !input.classList.contains('js-member-active-toggle')) return;
    var url = input.getAttribute('data-post-url');
    if (!url) return;

    var desired = input.checked;
    var label = input.closest('label');
    var textEl = label ? label.querySelector('.js-member-active-text') : null;

    fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify({ is_active: desired }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        if (res.ok && res.data && res.data.ok) {
          var active = !!res.data.is_active;
          input.checked = active;
          input.setAttribute('aria-checked', active ? 'true' : 'false');
          if (textEl) textEl.textContent = active ? 'Active' : 'Inactive';
          return;
        }
        input.checked = !desired;
        var msg = (res.data && res.data.error) || 'Could not update active status.';
        if (typeof window.__opsToast === 'function') {
          window.__opsToast(msg, 'error');
        } else {
          window.alert(msg);
        }
      })
      .catch(function () {
        input.checked = !desired;
        if (typeof window.__opsToast === 'function') {
          window.__opsToast('Network error.', 'error');
        } else {
          window.alert('Network error.');
        }
      });
  });
})();
