/**
 * Hardware inventory list pages: Issue / Revoke modals (row actions).
 * Load after datatable/common/datatable-core.js (uses OpsCenterDataTable.getCookie).
 */
(function () {
  'use strict';

  function getCookie(name) {
    if (window.OpsCenterDataTable && typeof window.OpsCenterDataTable.getCookie === 'function') {
      return window.OpsCenterDataTable.getCookie(name);
    }
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function submitHardwareIssue(payload) {
    var body = new URLSearchParams(payload);
    return fetch('/hardwareissue/issue/create/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
      },
      body: body.toString()
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, data: data };
      });
    });
  }

  function submitHardwareRevoke(revokeUrl, payload) {
    var body = new URLSearchParams(payload);
    return fetch(revokeUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
      },
      body: body.toString()
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, data: data };
      });
    });
  }

  function ensureIssueModal() {
    var existing = document.getElementById('hardware-issue-modal');
    if (existing) return existing;
    var wrapper = document.createElement('div');
    wrapper.id = 'hardware-issue-modal';
    wrapper.className = 'fixed inset-0 z-[90] hidden items-center justify-center bg-slate-900/50 p-4';
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.innerHTML = '' +
      '<div class="w-full max-w-lg rounded-xl bg-white shadow-2xl border border-slate-200">' +
      '  <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">' +
      '    <h3 class="text-lg font-semibold text-slate-800">Issue Hardware</h3>' +
      '    <button type="button" class="js-issue-close rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Close">✕</button>' +
      '  </div>' +
      '  <form id="hardware-issue-form" class="p-5 space-y-4">' +
      '    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">' +
      '      <div>' +
      '        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Component</label>' +
      '        <div id="issue-component-name" class="text-sm font-medium text-slate-800 break-words">—</div>' +
      '      </div>' +
      '      <div>' +
      '        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Team</label>' +
      '        <div id="issue-component-team" class="text-sm font-medium text-slate-800 break-words">—</div>' +
      '      </div>' +
      '    </div>' +
      '    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">' +
      '      <div>' +
      '        <label for="issue-quantity" class="block text-sm font-medium text-slate-700 mb-1.5">Quantity</label>' +
      '        <input id="issue-quantity" name="quantity" type="number" min="1" value="1" required class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-rose-500">' +
      '      </div>' +
      '      <div>' +
      '        <label for="issue-reason" class="block text-sm font-medium text-slate-700 mb-1.5">Reason</label>' +
      '        <input id="issue-reason" name="reason" type="text" required class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-rose-500" placeholder="Enter issue reason">' +
      '      </div>' +
      '    </div>' +
      '    <p id="issue-error" class="hidden text-sm text-red-600"></p>' +
      '    <div class="flex items-center justify-end gap-2 pt-1">' +
      '      <button type="button" class="js-issue-close inline-flex items-center justify-center px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-700 text-sm font-medium hover:bg-slate-50">Cancel</button>' +
      '      <button type="submit" class="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-rose-600 text-white text-sm font-medium hover:bg-rose-700">Issue</button>' +
      '    </div>' +
      '    <input type="hidden" id="issue-component-route" name="component_route">' +
      '    <input type="hidden" id="issue-component-id" name="component_id">' +
      '  </form>' +
      '</div>';
    document.body.appendChild(wrapper);
    return wrapper;
  }

  function openIssueModal(payload) {
    var modal = ensureIssueModal();
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.setAttribute('aria-hidden', 'false');
    document.getElementById('issue-component-name').textContent = payload.componentName || '—';
    document.getElementById('issue-component-team').textContent = payload.componentTeam || '—';
    document.getElementById('issue-component-route').value = payload.componentRoute || '';
    document.getElementById('issue-component-id').value = payload.componentId || '';
    document.getElementById('issue-quantity').value = '1';
    document.getElementById('issue-reason').value = '';
    document.getElementById('issue-error').classList.add('hidden');
    document.getElementById('issue-error').textContent = '';
    document.getElementById('issue-quantity').focus();
  }

  function closeIssueModal() {
    var modal = document.getElementById('hardware-issue-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.setAttribute('aria-hidden', 'true');
  }

  function ensureIssueResultModal() {
    var existing = document.getElementById('hardware-issue-result-modal');
    if (existing) return existing;
    var wrapper = document.createElement('div');
    wrapper.id = 'hardware-issue-result-modal';
    wrapper.className = 'fixed inset-0 z-[95] hidden items-center justify-center bg-slate-900/50 p-4';
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.innerHTML = '' +
      '<div class="w-full max-w-md rounded-xl bg-white shadow-2xl border border-slate-200">' +
      '  <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">' +
      '    <h3 id="issue-result-title" class="text-lg font-semibold text-slate-800">Issue Result</h3>' +
      '    <button type="button" class="js-issue-result-close rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Close">✕</button>' +
      '  </div>' +
      '  <div class="p-5 space-y-3">' +
      '    <div class="text-sm"><span class="text-slate-500">Team:</span> <span id="issue-result-team" class="font-medium text-slate-800">—</span></div>' +
      '    <div id="issue-result-message" class="text-sm text-slate-700"></div>' +
      '    <div class="flex justify-end pt-2">' +
      '      <button type="button" class="js-issue-result-close inline-flex items-center justify-center px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium hover:bg-slate-900">OK</button>' +
      '    </div>' +
      '  </div>' +
      '</div>';
    document.body.appendChild(wrapper);
    return wrapper;
  }

  function showIssueResultPopup(kind, team, message) {
    var modal = ensureIssueResultModal();
    var titleEl = document.getElementById('issue-result-title');
    var teamEl = document.getElementById('issue-result-team');
    var msgEl = document.getElementById('issue-result-message');
    titleEl.textContent = kind === 'success' ? 'Issue Successful' : 'Issue Failed';
    titleEl.className = kind === 'success' ? 'text-lg font-semibold text-emerald-700' : 'text-lg font-semibold text-rose-700';
    teamEl.textContent = team || '—';
    msgEl.textContent = message || (kind === 'success' ? 'Hardware issued.' : 'Issue failed.');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeIssueResultPopup() {
    var modal = document.getElementById('hardware-issue-result-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.setAttribute('aria-hidden', 'true');
  }

  function ensureRevokeModal() {
    var existing = document.getElementById('hardware-revoke-modal');
    if (existing) return existing;
    var wrapper = document.createElement('div');
    wrapper.id = 'hardware-revoke-modal';
    wrapper.className = 'fixed inset-0 z-[90] hidden items-center justify-center bg-slate-900/50 p-4';
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.innerHTML = '' +
      '<div class="w-full max-w-lg rounded-xl bg-white shadow-2xl border border-slate-200">' +
      '  <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">' +
      '    <h3 class="text-lg font-semibold text-slate-800">Revoke Issued Hardware</h3>' +
      '    <button type="button" class="js-revoke-close rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Close">✕</button>' +
      '  </div>' +
      '  <form id="hardware-revoke-form" class="p-5 space-y-4">' +
      '    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">' +
      '      <div>' +
      '        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Component</label>' +
      '        <div id="revoke-component-name" class="text-sm font-medium text-slate-800 break-words">—</div>' +
      '      </div>' +
      '      <div>' +
      '        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Team</label>' +
      '        <div id="revoke-component-team" class="text-sm font-medium text-slate-800 break-words">—</div>' +
      '      </div>' +
      '    </div>' +
      '    <div>' +
      '      <div class="text-xs text-slate-500 mb-1">Issued Quantity</div>' +
      '      <div id="revoke-max-qty" class="text-sm font-semibold text-slate-800">0</div>' +
      '    </div>' +
      '    <div>' +
      '      <label for="revoke-quantity" class="block text-sm font-medium text-slate-700 mb-1.5">Revoke Quantity</label>' +
      '      <input id="revoke-quantity" name="quantity" type="number" min="1" value="1" required class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500">' +
      '    </div>' +
      '    <p id="revoke-error" class="hidden text-sm text-red-600"></p>' +
      '    <div class="flex items-center justify-end gap-2 pt-1">' +
      '      <button type="button" class="js-revoke-close inline-flex items-center justify-center px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-700 text-sm font-medium hover:bg-slate-50">Cancel</button>' +
      '      <button type="submit" class="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700">Revoke</button>' +
      '    </div>' +
      '    <input type="hidden" id="revoke-url">' +
      '    <input type="hidden" id="revoke-max-qty-value">' +
      '  </form>' +
      '</div>';
    document.body.appendChild(wrapper);
    return wrapper;
  }

  function openRevokeModal(payload) {
    var modal = ensureRevokeModal();
    var maxQty = parseInt(payload.maxQty, 10);
    if (!maxQty || maxQty < 1) maxQty = 1;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.setAttribute('aria-hidden', 'false');
    document.getElementById('revoke-component-name').textContent = payload.componentName || '—';
    document.getElementById('revoke-component-team').textContent = payload.componentTeam || '—';
    document.getElementById('revoke-max-qty').textContent = String(maxQty);
    document.getElementById('revoke-url').value = payload.revokeUrl || '';
    document.getElementById('revoke-max-qty-value').value = String(maxQty);
    var qtyInput = document.getElementById('revoke-quantity');
    qtyInput.value = '1';
    qtyInput.setAttribute('max', String(maxQty));
    var errorEl = document.getElementById('revoke-error');
    errorEl.classList.add('hidden');
    errorEl.textContent = '';
    qtyInput.focus();
  }

  function closeRevokeModal() {
    var modal = document.getElementById('hardware-revoke-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.setAttribute('aria-hidden', 'true');
  }

  function ensureRevokeResultModal() {
    var existing = document.getElementById('hardware-revoke-result-modal');
    if (existing) return existing;
    var wrapper = document.createElement('div');
    wrapper.id = 'hardware-revoke-result-modal';
    wrapper.className = 'fixed inset-0 z-[95] hidden items-center justify-center bg-slate-900/50 p-4';
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.innerHTML = '' +
      '<div class="w-full max-w-md rounded-xl bg-white shadow-2xl border border-slate-200">' +
      '  <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">' +
      '    <h3 id="revoke-result-title" class="text-lg font-semibold text-slate-800">Revoke Result</h3>' +
      '    <button type="button" class="js-revoke-result-close rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Close">✕</button>' +
      '  </div>' +
      '  <div class="p-5 space-y-3">' +
      '    <div class="text-sm"><span class="text-slate-500">Team:</span> <span id="revoke-result-team" class="font-medium text-slate-800">—</span></div>' +
      '    <div id="revoke-result-message" class="text-sm text-slate-700"></div>' +
      '    <div class="flex justify-end pt-2">' +
      '      <button type="button" class="js-revoke-result-close inline-flex items-center justify-center px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium hover:bg-slate-900">OK</button>' +
      '    </div>' +
      '  </div>' +
      '</div>';
    document.body.appendChild(wrapper);
    return wrapper;
  }

  function showRevokeResultPopup(kind, team, message) {
    var modal = ensureRevokeResultModal();
    var titleEl = document.getElementById('revoke-result-title');
    var teamEl = document.getElementById('revoke-result-team');
    var msgEl = document.getElementById('revoke-result-message');
    titleEl.textContent = kind === 'success' ? 'Revoke Successful' : 'Revoke Failed';
    titleEl.className = kind === 'success' ? 'text-lg font-semibold text-emerald-700' : 'text-lg font-semibold text-rose-700';
    teamEl.textContent = team || '—';
    msgEl.textContent = message || (kind === 'success' ? 'Hardware revoked.' : 'Revoke failed.');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeRevokeResultPopup() {
    var modal = document.getElementById('hardware-revoke-result-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.setAttribute('aria-hidden', 'true');
  }

  function bindHardwareRowModals() {
    if (window.__hardwareIssueBound) return;
    window.__hardwareIssueBound = true;

    var modal = ensureIssueModal();
    var resultModal = ensureIssueResultModal();
    var revokeModal = ensureRevokeModal();
    var revokeResultModal = ensureRevokeResultModal();

    modal.addEventListener('click', function (event) {
      if (event.target === modal || event.target.closest('.js-issue-close')) {
        closeIssueModal();
      }
    });
    resultModal.addEventListener('click', function (event) {
      if (event.target === resultModal || event.target.closest('.js-issue-result-close')) {
        closeIssueResultPopup();
      }
    });
    revokeModal.addEventListener('click', function (event) {
      if (event.target === revokeModal || event.target.closest('.js-revoke-close')) {
        closeRevokeModal();
      }
    });
    revokeResultModal.addEventListener('click', function (event) {
      if (event.target === revokeResultModal || event.target.closest('.js-revoke-result-close')) {
        closeRevokeResultPopup();
      }
    });

    var issueForm = document.getElementById('hardware-issue-form');
    if (issueForm) {
      issueForm.addEventListener('submit', function (event) {
        event.preventDefault();
        var componentRoute = document.getElementById('issue-component-route').value;
        var componentId = document.getElementById('issue-component-id').value;
        var qty = parseInt(document.getElementById('issue-quantity').value, 10);
        var reason = (document.getElementById('issue-reason').value || '').trim();
        var errorEl = document.getElementById('issue-error');

        if (!componentRoute || !componentId) {
          errorEl.textContent = 'Invalid component selection.';
          errorEl.classList.remove('hidden');
          return;
        }
        if (!qty || qty < 1) {
          errorEl.textContent = 'Enter a valid quantity.';
          errorEl.classList.remove('hidden');
          return;
        }
        if (!reason) {
          errorEl.textContent = 'Reason is required.';
          errorEl.classList.remove('hidden');
          return;
        }

        submitHardwareIssue({
          component_route: componentRoute,
          component_id: componentId,
          quantity: String(qty),
          reason: reason
        }).then(function (result) {
          var teamText = document.getElementById('issue-component-team').textContent || '—';
          if (!result.ok) {
            var failMsg = result.data && result.data.error ? result.data.error : 'Issue failed.';
            errorEl.textContent = failMsg;
            errorEl.classList.remove('hidden');
            showIssueResultPopup('error', teamText, failMsg);
            return;
          }
          closeIssueModal();
          showIssueResultPopup('success', teamText, (result.data && result.data.message) || 'Hardware issued.');
          if (window.jQuery && window.jQuery.fn && window.jQuery.fn.dataTable) {
            window.jQuery('table[data-server-side][data-ajax-url]').each(function () {
              var dt = window.jQuery(this).DataTable();
              if (dt) dt.ajax.reload(null, false);
            });
          } else {
            window.location.reload();
          }
        }).catch(function () {
          var teamText = document.getElementById('issue-component-team').textContent || '—';
          errorEl.textContent = 'Issue request failed.';
          errorEl.classList.remove('hidden');
          showIssueResultPopup('error', teamText, 'Issue request failed.');
        });
      });
    }

    var revokeForm = document.getElementById('hardware-revoke-form');
    if (revokeForm) {
      revokeForm.addEventListener('submit', function (event) {
        event.preventDefault();
        var revokeUrl = document.getElementById('revoke-url').value;
        var maxQty = parseInt(document.getElementById('revoke-max-qty-value').value, 10);
        var qty = parseInt(document.getElementById('revoke-quantity').value, 10);
        var errorEl = document.getElementById('revoke-error');
        var teamText = document.getElementById('revoke-component-team').textContent || '—';

        if (!revokeUrl) {
          errorEl.textContent = 'Invalid revoke request.';
          errorEl.classList.remove('hidden');
          return;
        }
        if (!qty || qty < 1) {
          errorEl.textContent = 'Enter a valid quantity.';
          errorEl.classList.remove('hidden');
          return;
        }
        if (!maxQty || qty > maxQty) {
          errorEl.textContent = 'Revoke quantity cannot exceed issued quantity.';
          errorEl.classList.remove('hidden');
          return;
        }

        submitHardwareRevoke(revokeUrl, { quantity: String(qty) }).then(function (result) {
          if (!result.ok) {
            var failMsg = result.data && result.data.error ? result.data.error : 'Revoke failed.';
            errorEl.textContent = failMsg;
            errorEl.classList.remove('hidden');
            showRevokeResultPopup('error', teamText, failMsg);
            return;
          }
          closeRevokeModal();
          showRevokeResultPopup('success', teamText, (result.data && result.data.message) || 'Hardware revoked.');
          if (window.jQuery && window.jQuery.fn && window.jQuery.fn.dataTable) {
            window.jQuery('table[data-server-side][data-ajax-url]').each(function () {
              var dt = window.jQuery(this).DataTable();
              if (dt) dt.ajax.reload(null, false);
            });
          } else {
            window.location.reload();
          }
        }).catch(function () {
          errorEl.textContent = 'Revoke request failed.';
          errorEl.classList.remove('hidden');
          showRevokeResultPopup('error', teamText, 'Revoke request failed.');
        });
      });
    }

    document.addEventListener('click', function (event) {
      var btn = event.target.closest('.js-open-issue-modal');
      if (!btn) return;
      event.preventDefault();

      var componentName = btn.getAttribute('data-component-name') || 'component';
      var componentTeam = btn.getAttribute('data-component-team') || '—';
      var componentRoute = btn.getAttribute('data-component-route') || '';
      var componentId = btn.getAttribute('data-component-id') || '';
      if (!componentRoute || !componentId) return;
      openIssueModal({
        componentName: componentName,
        componentTeam: componentTeam,
        componentRoute: componentRoute,
        componentId: componentId
      });
    });

    document.addEventListener('click', function (event) {
      var btn = event.target.closest('.js-open-revoke-modal');
      if (!btn) return;
      event.preventDefault();
      var revokeUrl = btn.getAttribute('data-revoke-url') || '';
      var componentName = btn.getAttribute('data-component-name') || 'component';
      var componentTeam = btn.getAttribute('data-component-team') || '—';
      var maxQty = btn.getAttribute('data-revoke-qty') || '1';
      openRevokeModal({
        revokeUrl: revokeUrl,
        componentName: componentName,
        componentTeam: componentTeam,
        maxQty: maxQty
      });
    });
  }

  var $ = window.jQuery || window.$;
  if ($ && typeof $.fn !== 'undefined') {
    $(document).ready(bindHardwareRowModals);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindHardwareRowModals);
  } else {
    setTimeout(bindHardwareRowModals, 50);
  }
})();
