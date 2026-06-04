/**
 * Shared DataTables setup for all server-side list pages.
 * Requires: jQuery, jquery.dataTables.min.js (before this file).
 * Inits every table with data-server-side and data-ajax-url.
 */
(function () {
  'use strict';

  function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function initDataTable(tableEl) {
    var $ = window.jQuery || window.$;
    if (!$ || typeof $ !== 'function') return;
    var $table = $(tableEl);
    if (!$table.length) return;
    if (typeof $.fn.dataTable !== 'undefined' && typeof $.fn.dataTable.isDataTable === 'function' && $.fn.dataTable.isDataTable($table[0])) return;

    var ajaxUrl = $table.data('ajax-url');
    if (!ajaxUrl) return;

    var useTeamFilter = $table.attr('data-team-filter') === 'true';

    function mergeGlobalFilterParams(d) {
      var form = document.getElementById('globalFilterForm');
      if (form) {
        [
          'team',
          'department',
          'designation',
          'member',
          'date_from',
          'date_to',
          'date_preset',
        ].forEach(function (key) {
          var el = form.elements.namedItem(key);
          if (el && el.value !== '' && el.value != null) {
            d[key] = el.value;
          }
        });
        return;
      }
      if (useTeamFilter) {
        var teamEl = document.getElementById('hardwareTeamFilter');
        if (teamEl && teamEl.value) {
          d.team = teamEl.value;
        }
      }
    }

    var colCount = $table.find('thead th').length;
    if (!colCount) return;
    var lastIdx = colCount - 1;
    var allColumnsInteractive = $table.attr('data-all-columns-interactive') === 'true';
    var nonOrderableRaw = $table.attr('data-non-orderable-cols') || '';
    var nonOrderable = {};
    if (nonOrderableRaw) {
      nonOrderableRaw.split(',').forEach(function (part) {
        var n = parseInt(String(part).trim(), 10);
        if (!isNaN(n) && n >= 0) {
          nonOrderable[n] = true;
        }
      });
    }
    var initialOrderCol = parseInt($table.attr('data-initial-order-col'), 10);
    var initialOrderDir = ($table.attr('data-initial-order-dir') || 'desc').toLowerCase() === 'asc' ? 'asc' : 'desc';
    var initialOrder = [[0, 'desc']];
    if (!isNaN(initialOrderCol) && initialOrderCol >= 0 && initialOrderCol < colCount) {
      initialOrder = [[initialOrderCol, initialOrderDir]];
    }

    var columns = [];
    var colWidthPct = (100 / colCount).toFixed(2) + '%';
    var actionsColWidth = '9rem';
    for (var i = 0; i < colCount; i++) {
      columns.push({
        data: i,
        orderable: (allColumnsInteractive || i !== lastIdx) && !nonOrderable[i],
        searchable: allColumnsInteractive || i !== lastIdx,
        width: i === lastIdx ? actionsColWidth : colWidthPct
      });
    }

    var ajaxConfig = {
      url: ajaxUrl,
      type: 'GET',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      data: function (d) {
        mergeGlobalFilterParams(d);
      },
    };

    var table = $table.DataTable({
      autoWidth: false,
      serverSide: true,
      ajax: ajaxConfig,

      pageLength: 25,
      lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, 'All']],
      order: initialOrder,
      scrollX: true,
      scrollCollapse: true,
      processing: true,
      stateSave: true,

      dom: '<"grid grid-cols-3 items-center p-4 border-b border-slate-200"l<"flex justify-center"f><"flex justify-end">>rt<"flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border-t border-slate-200 bg-slate-50/50"ip>',

      language: {
        search: '',
        searchPlaceholder: '🔍 Search...',
        lengthMenu: 'Show _MENU_ entries',

        info: '<span class="text-slate-600 text-sm">Showing _START_ to _END_ of _TOTAL_ entries</span>',
        infoEmpty: '<span class="text-slate-400 text-sm">No entries available</span>',
        infoFiltered: '<span class="text-slate-400 text-xs">(filtered from _MAX_ total)</span>',

        zeroRecords: `
      <div class="py-20 text-center">
        <div class="text-blue-300 text-5xl mb-3">🔍</div>
        <div class="text-slate-700 font-semibold text-base">
          No matching records
        </div>
        <div class="text-slate-400 text-sm mt-1">
          Try adjusting your search
        </div>
      </div>
    `,

        emptyTable: 'No data available',

        processing: `
      <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-transparent mr-2 align-middle"></span>
      Loading...
    `,

        paginate: {
          first: '«',
          last: '»',
          previous: '← Prev',
          next: 'Next →'
        }
      },

      columns: columns,

      drawCallback: function () {
        table.columns.adjust();

        var wrapper = $table.closest('.dataTables_wrapper');

        wrapper.find('.dataTables_paginate .paginate_button')
          .addClass('px-3 py-1 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-indigo-50 hover:border-indigo-400 transition');

        wrapper.find('.dataTables_paginate .current')
          .removeClass()
          .addClass('paginate_button current px-3 py-1 rounded-lg border border-blue-200 bg-white text-slate-700');

        wrapper.find('.dataTables_paginate .paginate_button.disabled')
          .addClass('opacity-40 cursor-not-allowed');

        wrapper.find('.dataTables_length')
          .addClass('flex items-center gap-2 text-sm text-slate-600');

        wrapper.find('.dataTables_length select')
          .addClass(`
    px-3 py-1.5 rounded-lg border border-slate-200
    bg-white text-slate-700
    focus:outline-none focus:ring-2 focus:ring-indigo-400
    cursor-pointer
  `);
      }
    });

    $table.closest('.dataTables_wrapper').find('.dataTables_filter').addClass('mb-3');
    $table.closest('.dataTables_wrapper').find('.dataTables_length').addClass('mb-3');
  }

  function initAllDataTables() {
    var $ = window.jQuery || window.$;
    if (!$ || typeof $ !== 'function') return;
    $('table[data-server-side][data-ajax-url]').each(function () {
      initDataTable(this);
    });
  }

  window.OpsCenterDataTable = {
    getCookie: getCookie,
    initDataTable: initDataTable,
    initAll: initAllDataTables
  };

  var $ = window.jQuery || window.$;
  if ($ && typeof $.fn.DataTable !== 'undefined') {
    $(document).ready(initAllDataTables);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      if (window.jQuery && typeof window.jQuery.fn.DataTable !== 'undefined') initAllDataTables();
    });
  } else {
    setTimeout(function () {
      if (window.jQuery && typeof window.jQuery.fn.DataTable !== 'undefined') initAllDataTables();
    }, 50);
  }
})();
