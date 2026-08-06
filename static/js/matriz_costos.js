/* Matriz de costos: recálculo Material/Servicio + columnas colapsables */
(function () {
  'use strict';

  var PCT_KEYS = [
    'maquila',
    'instalacion',
    'desinstalacion',
    'ferreteria',
    'flete',
    'gg',
    'utilidad',
  ];

  function num(el) {
    if (!el) return 0;
    var v = parseFloat(String(el.value).replace(',', '.'));
    return isNaN(v) ? 0 : v;
  }

  function fmt(n) {
    return (Math.round(n * 100) / 100).toFixed(2);
  }

  function setReadonly(el, value) {
    if (!el) return;
    el.value = fmt(value);
  }

  function recalcRow(row) {
    var tipoEl = row.querySelector('.matriz-tipo, [name="tipo"]');
    var tipo = tipoEl ? tipoEl.value : 'material';
    var cantidad = num(row.querySelector('.matriz-cantidad, [name="cantidad"]'));
    var costo = num(row.querySelector('.matriz-costo_insumo, [name="costo_insumo"]'));
    var netoEl = row.querySelector('.matriz-neto_unidad, [name="neto_unidad"]');
    var precioEl = row.querySelector('[name="precio_unitario"]');

    var isServicio = tipo === 'servicio';
    row.classList.toggle('matriz-servicio', isServicio);
    row.classList.toggle('matriz-material', !isServicio);

    row.querySelectorAll('.matriz-pct-wrap input, .matriz-costo-wrap input, [name^="pct_"], [name="costo_insumo"]').forEach(function (inp) {
      if (!inp.name || inp.name === 'neto_unidad' || inp.name === 'utilidad_manual' || inp.name === 'precio_unitario') {
        return;
      }
      if (isServicio) {
        if (inp.name.indexOf('pct_') === 0 || inp.name === 'costo_insumo') {
          inp.value = '0';
          inp.readOnly = true;
        }
      } else if (inp.name.indexOf('pct_') === 0 || inp.name === 'costo_insumo') {
        inp.readOnly = false;
      }
    });

    if (isServicio) {
      PCT_KEYS.forEach(function (key) {
        setReadonly(row.querySelector('.matriz-vu-' + key), 0);
        setReadonly(row.querySelector('.matriz-tot-' + key), 0);
      });
      var neto = num(netoEl);
      if (precioEl) precioEl.value = fmt(neto);
      setReadonly(row.querySelector('.matriz-subtotal'), cantidad * neto);
      if (netoEl) {
        netoEl.readOnly = false;
        netoEl.classList.remove('matriz-calc');
      }
      return;
    }

    if (netoEl) {
      netoEl.readOnly = true;
      netoEl.classList.add('matriz-calc');
    }

    var pctSum = 0;
    PCT_KEYS.forEach(function (key) {
      var pct = num(row.querySelector('.matriz-pct_' + key + ', [name="pct_' + key + '"]'));
      pctSum += pct / 100;
      var vu = costo * (pct / 100);
      setReadonly(row.querySelector('.matriz-vu-' + key), vu);
      setReadonly(row.querySelector('.matriz-tot-' + key), vu * cantidad);
    });

    var neto = costo * (1 + pctSum);
    setReadonly(netoEl, neto);
    if (precioEl) precioEl.value = fmt(neto);
    setReadonly(row.querySelector('.matriz-subtotal'), cantidad * neto);
  }

  function bindRow(row) {
    row.querySelectorAll('input, select').forEach(function (el) {
      el.addEventListener('input', function () {
        recalcRow(row);
      });
      el.addEventListener('change', function () {
        recalcRow(row);
      });
    });
    recalcRow(row);
  }

  function bindCollapse(root) {
    root.querySelectorAll('[data-matriz-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var group = btn.getAttribute('data-matriz-toggle');
        var expanded = btn.getAttribute('aria-expanded') !== 'false';
        var next = !expanded;
        btn.setAttribute('aria-expanded', next ? 'true' : 'false');
        btn.textContent = next ? '−' : '+';
        root.querySelectorAll('[data-matriz-group="' + group + '"]').forEach(function (cell) {
          if (cell.classList.contains('matriz-col-pct')) return;
          cell.style.display = next ? '' : 'none';
        });
      });
    });
  }

  function init(root) {
    root = root || document;
    root.querySelectorAll('.matriz-row, .matriz-form').forEach(bindRow);
    bindCollapse(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init(document);
    });
  } else {
    init(document);
  }

  window.MatrizCostos = { init: init, recalcRow: recalcRow };
})();
