/**
 * Mobile sidebar open/close: toggle button and backdrop.
 * Targets #sidebar, #sidebar-backdrop, #sidebar-toggle.
 */
(function () {
  'use strict';

  function init() {
    var sidebar = document.getElementById('sidebar');
    var backdrop = document.getElementById('sidebar-backdrop');
    var toggle = document.getElementById('sidebar-toggle');
    if (!sidebar || !backdrop || !toggle) return;

    function open() {
      sidebar.classList.remove('-translate-x-full');
      backdrop.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    }

    function close() {
      sidebar.classList.add('-translate-x-full');
      backdrop.classList.add('hidden');
      document.body.style.overflow = '';
    }

    toggle.addEventListener('click', function () {
      if (sidebar.classList.contains('-translate-x-full')) {
        open();
      } else {
        close();
      }
    });
    backdrop.addEventListener('click', close);
    window.addEventListener('resize', function () {
      if (window.innerWidth >= 1024) close();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
