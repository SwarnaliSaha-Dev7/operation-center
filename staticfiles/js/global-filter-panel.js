/**
 * Global filter: modal UI, date range select, POST apply (session + redirect).
 */
(function () {
  'use strict';

  function syncPresetFromSelect(presetInput, dateRange, dateFrom, dateTo, customBox) {
    var v = (dateRange && dateRange.value) || '';
    if (presetInput) presetInput.value = v;
    if (v === 'custom') {
      if (customBox) {
        customBox.classList.remove('gf-custom-dates--hidden');
        customBox.classList.add('gf-custom-dates--visible');
      }
    } else {
      if (dateFrom) dateFrom.value = '';
      if (dateTo) dateTo.value = '';
      if (customBox) {
        customBox.classList.add('gf-custom-dates--hidden');
        customBox.classList.remove('gf-custom-dates--visible');
      }
    }
  }

  function openModal(modal, previouslyFocused) {
    if (!modal) return;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('gf-modal-open');
    modal._gfPreviousFocus = previouslyFocused || document.activeElement;
    var closeBtn = document.getElementById('globalFilterModalClose');
    if (closeBtn) closeBtn.focus();
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('gf-modal-open');
    var prev = modal._gfPreviousFocus;
    if (prev && typeof prev.focus === 'function') {
      try {
        prev.focus();
      } catch (e) {}
    }
  }

  function init() {
    var form = document.getElementById('globalFilterForm');
    var modal = document.getElementById('globalFilterModal');
    if (!form || !modal) return;

    var openBtn = document.getElementById('globalFilterOpen');
    var backdrop = document.getElementById('globalFilterBackdrop');
    var closeBtn = document.getElementById('globalFilterModalClose');
    var cancelBtn = document.getElementById('globalFilterCancel');
    var presetInput = document.getElementById('gf_date_preset');
    var dateRange = document.getElementById('gf_date_range');
    var customBox = document.getElementById('gfCustomDates');
    var dateFrom = document.getElementById('gf_date_from');
    var dateTo = document.getElementById('gf_date_to');

    if (dateRange) {
      dateRange.addEventListener('change', function () {
        syncPresetFromSelect(presetInput, dateRange, dateFrom, dateTo, customBox);
      });
    }

    if (dateRange && presetInput) {
      var hasDates = (dateFrom && dateFrom.value) || (dateTo && dateTo.value);
      var preset = presetInput.value || '';
      var numeric =
        preset === '3' ||
        preset === '7' ||
        preset === '15' ||
        preset === '30' ||
        preset === '180';
      if (hasDates && !numeric && preset !== 'custom') {
        dateRange.value = 'custom';
        presetInput.value = 'custom';
        if (customBox) {
          customBox.classList.remove('gf-custom-dates--hidden');
          customBox.classList.add('gf-custom-dates--visible');
        }
      }
    }

    form.addEventListener('submit', function () {
      syncPresetFromSelect(presetInput, dateRange, dateFrom, dateTo, customBox);
    });

    if (openBtn) {
      openBtn.addEventListener('click', function () {
        openModal(modal, openBtn);
      });
    }
    if (backdrop) {
      backdrop.addEventListener('click', function () {
        closeModal(modal);
      });
    }
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        closeModal(modal);
      });
    }
    if (cancelBtn) {
      cancelBtn.addEventListener('click', function () {
        closeModal(modal);
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      if (!modal.classList.contains('is-open')) return;
      closeModal(modal);
    });

    var clearAll = document.getElementById('globalFilterClear');
    var clearForm = document.getElementById('globalFilterClearForm');
    var clearNext = document.getElementById('gf_clear_next');
    if (clearAll && clearForm) {
      clearAll.addEventListener('click', function () {
        if (clearNext) {
          clearNext.value = window.location.pathname + window.location.search;
        }
        clearForm.submit();
      });
    }

    syncPresetFromSelect(presetInput, dateRange, dateFrom, dateTo, customBox);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
