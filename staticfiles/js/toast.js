/**
 * Auto-dismiss toasts in #toast-container (Django messages).
 * Run on DOMContentLoaded; no-op if container missing.
 */
(function () {
  'use strict';

  function init() {
    var container = document.getElementById('toast-container');
    if (!container) return;
    var toasts = container.querySelectorAll('[data-toast]');
    var delay = 4500;
    var transitionMs = 300;
    toasts.forEach(function (toast) {
      setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(function () {
          toast.remove();
          if (container.querySelectorAll('[data-toast]').length === 0) {
            container.remove();
          }
        }, transitionMs);
      }, delay);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
