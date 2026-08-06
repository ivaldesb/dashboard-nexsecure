/* Modales NexSecure: crear/editar sin salir de la pestaña */
(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function modalEls() {
    return {
      root: qs('#nxModal'),
      title: qs('#nxModalTitle'),
      body: qs('#nxModalBody'),
    };
  }

  function withModalParam(url) {
    var u = new URL(url, window.location.origin);
    u.searchParams.set('modal', '1');
    return u.toString();
  }

  function setLoading(body) {
    body.innerHTML =
      '<div class="nx-modal-loading text-center" style="padding:28px;color:#64748b">' +
      '<i class="fa fa-spinner fa-spin"></i> Cargando…</div>';
  }

  function bindForm(body) {
    var form = qs('form[data-nx-modal-form]', body);
    if (!form) return;
    form.addEventListener('submit', onSubmit);
    if (window.MatrizCostos && typeof window.MatrizCostos.init === 'function') {
      window.MatrizCostos.init(form);
    }
    if (typeof window.nxInitSelect2 === 'function') {
      window.nxInitSelect2(body);
    }
  }

  function openModal(url, titleHint) {
    var els = modalEls();
    if (!els.root || !window.jQuery) {
      window.location.href = url;
      return;
    }
    els.title.textContent = titleHint || 'Formulario';
    setLoading(els.body);
    window.jQuery(els.root).modal('show');

    fetch(withModalParam(url), {
      headers: { 'X-NX-Modal': '1', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (html) {
        els.body.innerHTML = html;
        var h = qs('[data-nx-modal-title]', els.body);
        if (h && h.textContent) els.title.textContent = h.textContent.trim();
        else if (titleHint) els.title.textContent = titleHint;
        bindForm(els.body);
      })
      .catch(function () {
        els.body.innerHTML =
          '<div class="alert alert-danger">No se pudo cargar el formulario. <a href="' +
          url +
          '">Abrir página</a></div>';
      });
  }

  function onSubmit(ev) {
    ev.preventDefault();
    var form = ev.currentTarget;
    var els = modalEls();
    var btn = qs('button[type="submit"]', form);
    if (btn) {
      btn.disabled = true;
      btn.dataset.label = btn.textContent;
      btn.textContent = 'Guardando…';
    }

    var fd = new FormData(form);
    if (!fd.get('modal')) fd.append('modal', '1');

    fetch(form.action || window.location.href, {
      method: 'POST',
      body: fd,
      headers: { 'X-NX-Modal': '1', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
      .then(function (r) {
        var ct = r.headers.get('Content-Type') || '';
        if (ct.indexOf('application/json') !== -1) {
          return r.json().then(function (data) {
            return { json: data };
          });
        }
        return r.text().then(function (html) {
          return { html: html, ok: r.ok };
        });
      })
      .then(function (res) {
        if (res.json && res.json.ok) {
          window.jQuery(els.root).modal('hide');
          window.location.href = res.json.redirect || window.location.href;
          return;
        }
        if (res.html) {
          els.body.innerHTML = res.html;
          bindForm(els.body);
        }
      })
      .catch(function () {
        if (btn) {
          btn.disabled = false;
          btn.textContent = btn.dataset.label || 'Guardar';
        }
        alert('Error al guardar. Intenta de nuevo.');
      });
  }

  function onClick(ev) {
    var a = ev.target.closest('a[data-nx-modal]');
    if (!a) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || a.target === '_blank') return;
    ev.preventDefault();
    openModal(a.getAttribute('href'), a.getAttribute('data-nx-modal-title') || a.textContent.trim());
  }

  document.addEventListener('click', onClick);
})();
