/* Picker M2M: arriba disponibles (buscar/añadir), abajo asignados (con X). */
(function () {
  'use strict';

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function ensureMultiple(select) {
    if (!select.multiple) select.multiple = true;
  }

  function buildPicker(select) {
    if (select.dataset.nxM2mReady === '1') return;
    ensureMultiple(select);
    select.dataset.nxM2mReady = '1';
    select.classList.add('nx-m2m-native');
    select.setAttribute('aria-hidden', 'true');
    select.tabIndex = -1;

    var wrap = document.createElement('div');
    wrap.className = 'nx-m2m';
    wrap.dataset.for = select.id || select.name;

    var placeholder =
      select.getAttribute('data-placeholder') || 'Buscar para añadir…';

    wrap.innerHTML =
      '<div class="nx-m2m-add">' +
      '<label class="nx-m2m-label">Disponibles</label>' +
      '<input type="search" class="form-control nx-m2m-search" placeholder="' +
      escapeHtml(placeholder) +
      '" autocomplete="off">' +
      '<ul class="nx-m2m-available"></ul>' +
      '</div>' +
      '<div class="nx-m2m-selected-wrap">' +
      '<label class="nx-m2m-label">Asignados</label>' +
      '<ul class="nx-m2m-selected"></ul>' +
      '<p class="nx-m2m-empty text-muted">Ninguno asignado aún.</p>' +
      '</div>';

    select.parentNode.insertBefore(wrap, select.nextSibling);

    var search = wrap.querySelector('.nx-m2m-search');
    var availUl = wrap.querySelector('.nx-m2m-available');
    var selUl = wrap.querySelector('.nx-m2m-selected');
    var empty = wrap.querySelector('.nx-m2m-empty');

    function options() {
      return Array.prototype.slice.call(select.options);
    }

    function render() {
      var q = (search.value || '').trim().toLowerCase();
      availUl.innerHTML = '';
      selUl.innerHTML = '';
      var selectedCount = 0;

      options().forEach(function (opt) {
        if (!opt.value) return;
        var label = opt.textContent.trim();
        if (opt.selected) {
          selectedCount += 1;
          var li = document.createElement('li');
          li.className = 'nx-m2m-chip';
          li.innerHTML =
            '<span class="nx-m2m-chip-label">' +
            escapeHtml(label) +
            '</span>' +
            '<button type="button" class="nx-m2m-remove" title="Quitar" aria-label="Quitar">&times;</button>';
          li.querySelector('.nx-m2m-remove').addEventListener('click', function () {
            opt.selected = false;
            render();
            select.dispatchEvent(new Event('change', { bubbles: true }));
          });
          selUl.appendChild(li);
        } else {
          if (q && label.toLowerCase().indexOf(q) === -1) return;
          var liA = document.createElement('li');
          liA.className = 'nx-m2m-option';
          liA.innerHTML =
            '<span>' +
            escapeHtml(label) +
            '</span>' +
            '<button type="button" class="btn btn-xs btn-primary nx-m2m-add-btn">Añadir</button>';
          liA.querySelector('.nx-m2m-add-btn').addEventListener('click', function () {
            opt.selected = true;
            search.value = '';
            render();
            select.dispatchEvent(new Event('change', { bubbles: true }));
            search.focus();
          });
          availUl.appendChild(liA);
        }
      });

      if (!availUl.children.length) {
        var none = document.createElement('li');
        none.className = 'nx-m2m-none text-muted';
        none.textContent = q ? 'Sin coincidencias' : 'No hay más para añadir';
        availUl.appendChild(none);
      }
      empty.style.display = selectedCount ? 'none' : 'block';
      selUl.style.display = selectedCount ? 'block' : 'none';
    }

    search.addEventListener('input', render);
    render();
  }

  function enhanceSearchSelect(select) {
    if (select.dataset.nxSearchReady === '1') return;
    if (select.multiple) return;
    select.dataset.nxSearchReady = '1';
    var wrap = document.createElement('div');
    wrap.className = 'nx-select-search-wrap';
    var filter = document.createElement('input');
    filter.type = 'search';
    filter.className = 'form-control nx-select-filter';
    filter.placeholder = select.getAttribute('data-placeholder') || 'Filtrar opciones…';
    filter.autocomplete = 'off';
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(filter);
    wrap.appendChild(select);

    var all = Array.prototype.map.call(select.options, function (o) {
      return { value: o.value, text: o.text, selected: o.selected, disabled: o.disabled };
    });

    function apply() {
      var q = (filter.value || '').trim().toLowerCase();
      var current = select.value;
      select.innerHTML = '';
      all.forEach(function (o) {
        if (o.value && q && o.text.toLowerCase().indexOf(q) === -1 && o.value !== current) {
          return;
        }
        var opt = document.createElement('option');
        opt.value = o.value;
        opt.textContent = o.text;
        opt.disabled = o.disabled;
        if (o.value === current) opt.selected = true;
        select.appendChild(opt);
      });
    }

    filter.addEventListener('input', apply);
  }

  function init(root) {
    var scope = root || document;
    scope.querySelectorAll('select.nx-m2m-picker').forEach(buildPicker);
    scope.querySelectorAll('select.nx-select-search').forEach(enhanceSearchSelect);
  }

  window.nxInitSelect2 = init; // alias para nx-modal.js
  window.nxInitM2mPicker = init;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init(document);
    });
  } else {
    init(document);
  }
})();
