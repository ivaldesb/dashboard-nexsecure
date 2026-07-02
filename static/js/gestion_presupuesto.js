$(document).ready(function() {
    // Variables globales
    let currentItemId = null;
    let currentPagoId = null;

    // Función para calcular costos
    function calcularCostos() {
        const insumos = parseFloat($('#costo_insumos').val() || 0);
        const maquila = parseFloat($('#costo_maquila').val() || 0);
        const instalacion = parseFloat($('#costo_instalacion').val() || 0);
        const desinstalacion = parseFloat($('#costo_desinstalacion').val() || 0);
        const materiales = parseFloat($('#costo_materiales').val() || 0);
        const gastos = parseFloat($('#costo_gastos').val() || 0);
        const utilidad = parseFloat($('#costo_utilidad').val() || 0);
        const flete = parseFloat($('#costo_flete').val() || 0);

        const totalSinUtilidad = insumos + maquila + instalacion + desinstalacion + materiales + gastos + flete;
        const utilidadMonto = totalSinUtilidad * (utilidad / 100);
        const valorConUtilidad = totalSinUtilidad + utilidadMonto;

        $('#costo_total_sin_utilidad').val('$ ' + totalSinUtilidad.toLocaleString('es-CL', {maximumFractionDigits: 0}));
        $('#costo_valor_con_utilidad').val('$ ' + valorConUtilidad.toLocaleString('es-CL', {maximumFractionDigits: 0}));
    }

    // Event listeners para cálculo automático de costos
    $('#costo_insumos, #costo_maquila, #costo_instalacion, #costo_desinstalacion, #costo_materiales, #costo_gastos, #costo_utilidad, #costo_flete').on('input', calcularCostos);

    // Abrir modal para editar costos
    $('.btn-edit-costo').on('click', function() {
        const itemId = $(this).data('item-id');
        currentItemId = itemId;
        const row = $(this).closest('tr');
        
        // Cargar valores actuales
        $('#costo_item_id').val(itemId);
        $('#costo_insumos').val(parseFloat(row.find('.costo-insumos').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_maquila').val(parseFloat(row.find('.costo-maquila').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_instalacion').val(parseFloat(row.find('.costo-instalacion').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_desinstalacion').val(parseFloat(row.find('.costo-desinstalacion').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_materiales').val(parseFloat(row.find('.costo-materiales').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_gastos').val(parseFloat(row.find('.costo-gastos').text().replace(/[^0-9.-]/g, '')) || 0);
        $('#costo_utilidad').val(parseFloat(row.find('.costo-utilidad').text().replace('%', '')) || 0);
        $('#costo_flete').val(parseFloat(row.find('.costo-flete').text().replace(/[^0-9.-]/g, '')) || 0);
        
        calcularCostos();
        $('#modalEditCosto').modal('show');
    });

    // Guardar costos
    $('#btnSaveCosto').on('click', function() {
        const data = {
            item_id: $('#costo_item_id').val(),
            insumos: $('#costo_insumos').val(),
            maquila: $('#costo_maquila').val(),
            instalacion: $('#costo_instalacion').val(),
            desinstalacion: $('#costo_desinstalacion').val(),
            materiales_ferreteria: $('#costo_materiales').val(),
            gastos_generales: $('#costo_gastos').val(),
            utilidad_porcentaje: $('#costo_utilidad').val(),
            flete: $('#costo_flete').val()
        };

        $.ajax({
            url: '/api/presupuesto/costo',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error al guardar los costos');
            }
        });
    });

    // Variable para rastrear si estamos editando
    let currentGastoId = null;

    // Abrir modal para editar gasto
    $(document).on('click', '.btn-edit-gasto', function() {
        const gastoId = $(this).data('gasto-id');
        currentGastoId = gastoId;
        
        // Obtener datos del gasto desde el servidor
        $.ajax({
            url: '/api/presupuesto/gasto/' + gastoId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    const gasto = response.data;
                    $('#gasto_id').val(gasto.id);
                    $('#formAddGasto [name="descripcion"]').val(gasto.descripcion);
                    $('#formAddGasto [name="monto"]').val(gasto.monto);
                    $('#formAddGasto [name="tipo"]').val(gasto.tipo);
                    // Manejar pagado_por_id: None = '', 'empresa' = 'empresa', ID = ID
                    const pagadoPorId = gasto.pagado_por_id || '';
                    $('#gasto_pagado_por').val(pagadoPorId);
                    $('#formAddGasto [name="fecha"]').val(gasto.fecha || '');
                    // Cargar factura_id si existe
                    $('#gasto_factura_id').val(gasto.factura_id || '');
                    
                    $('#modalGastoTitle').text('Editar Gasto');
                    $('#modalAddGasto').modal('show');
                } else {
                    alert('Error al cargar los datos del gasto: ' + (response.message || 'Error desconocido'));
                }
            },
            error: function() {
                alert('Error al cargar los datos del gasto');
            }
        });
    });

    // Limpiar formulario al cerrar modal
    $('#modalAddGasto').on('hidden.bs.modal', function() {
        $('#formAddGasto')[0].reset();
        $('#gasto_id').val('');
        currentGastoId = null;
        $('#modalGastoTitle').text('Agregar Gasto');
    });

    // Agregar o editar gasto
    $('#btnSaveGasto').on('click', function() {
        const gastoId = $('#gasto_id').val();
        const formData = {
            descripcion: $('#formAddGasto [name="descripcion"]').val(),
            monto: parseChileanNumber($('#formAddGasto [name="monto"]').val()),
            tipo: $('#formAddGasto [name="tipo"]').val(),
            pagado_por_id: $('#formAddGasto [name="pagado_por_id"]').val() || null,
            pagado_por_tipo: 'user',
            fecha: $('#formAddGasto [name="fecha"]').val(),
            factura_id: $('#gasto_factura_id').val() || null
        };

        const url = gastoId ? '/api/presupuesto/gasto/' + gastoId : '/api/presupuesto/gasto';
        const method = gastoId ? 'PUT' : 'POST';

        // Si es nuevo, agregar presupuesto_id
        if (!gastoId) {
            formData.presupuesto_id = presupuestoId;
        }

        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error al ' + (gastoId ? 'actualizar' : 'agregar') + ' el gasto');
            }
        });
    });

    // Eliminar gasto
    $('.btn-delete-gasto').on('click', function() {
        if (!confirm('¿Está seguro de eliminar este gasto?')) return;
        
        const gastoId = $(this).data('gasto-id');
        $.ajax({
            url: '/api/presupuesto/gasto/' + gastoId,
            method: 'DELETE',
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error al eliminar el gasto');
                }
            },
            error: function() {
                alert('Error al eliminar el gasto');
            }
        });
    });

    // Abrir modal para editar pago - cargar datos desde el servidor
    $(document).on('click', '.btn-edit-pago', function() {
        const pagoId = $(this).data('pago-id');
        const empleadoId = $(this).data('empleado-id');
        currentPagoId = pagoId;
        
        // Obtener datos del pago desde el servidor
        $.ajax({
            url: '/api/presupuesto/pago-empleado/' + pagoId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    const pago = response.data;
                    $('#pago_empleado_id').val(pago.empleado_id || empleadoId);
                    $('#pago_porcentaje').val(pago.porcentaje_pago || 0);
                    $('#pago_anticipo').val(pago.anticipo || 0);
                    $('#pago_quien_pago').val(pago.quien_pago_anticipo_id || '');
                    
                    $('#modalPagoEmpleadoTitle').text('Editar Pago a Empleado');
                    $('#pago_empleado_id').prop('disabled', true);
                    $('#modalAddPagoEmpleado').modal('show');
                } else {
                    alert('Error al cargar los datos del pago: ' + (response.message || 'Error desconocido'));
                }
            },
            error: function(xhr, status, error) {
                console.error('Error al cargar pago:', error);
                console.error('Response:', xhr.responseText);
                alert('Error al cargar los datos del pago. Ver consola para más detalles.');
            }
        });
    });

    // Resetear modal al cerrar
    $('#modalAddPagoEmpleado').on('hidden.bs.modal', function() {
        $('#formAddPagoEmpleado')[0].reset();
        $('#modalPagoEmpleadoTitle').text('Agregar Pago a Empleado');
        $('#pago_empleado_id').prop('disabled', false);
        currentPagoId = null;
    });

    // Agregar/Editar pago empleado
    $('#btnSavePagoEmpleado').on('click', function() {
        const formData = {
            presupuesto_id: presupuestoId,
            empleado_id: $('#formAddPagoEmpleado [name="empleado_id"]').val(),
            porcentaje_pago: $('#formAddPagoEmpleado [name="porcentaje_pago"]').val(),
            anticipo: $('#formAddPagoEmpleado [name="anticipo"]').val(),
            quien_pago_anticipo_id: $('#formAddPagoEmpleado [name="quien_pago_anticipo_id"]').val() || null
        };

        $.ajax({
            url: '/api/presupuesto/pago-empleado',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error al guardar el pago');
            }
        });
    });

    // Eliminar pago empleado
    $('.btn-delete-pago').on('click', function() {
        if (!confirm('¿Está seguro de eliminar este pago?')) return;
        
        const pagoId = $(this).data('pago-id');
        $.ajax({
            url: '/api/presupuesto/pago-empleado/' + pagoId,
            method: 'DELETE',
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error al eliminar el pago');
                }
            },
            error: function() {
                alert('Error al eliminar el pago');
            }
        });
    });

    // Calcular resumen
    function actualizarResumen() {
        let totalPagos = 0;
        $('.pago-total').each(function() {
            const valor = parseFloat($(this).text().replace(/[^0-9.-]/g, '')) || 0;
            totalPagos += valor;
        });

        $('#resumenTotalPagos').text(totalPagos.toLocaleString('es-CL', {maximumFractionDigits: 0}));
        
        // Calcular diferencia (lo que recibe la empresa)
        const montoEmpresaUtilidad = parseFloat($('#resumenMontoEmpresaUtilidad').text().replace(/[^0-9.-]/g, '') || 0);
        const gastosEmpresa = parseFloat($('#resumenGastosEmpresa').text().replace(/[^0-9.-]/g, '') || 0);
        const diferencia = montoEmpresaUtilidad + gastosEmpresa;
        
        $('#resumenDiferencia').text(diferencia.toLocaleString('es-CL', {maximumFractionDigits: 0}));
        
        // Cambiar color según si es positivo o negativo
        const diferenciaSpan = $('#resumenDiferenciaSpan');
        if (diferencia >= 0) {
            diferenciaSpan.css('color', '#90EE90'); // Verde claro
        } else {
            diferenciaSpan.css('color', '#FFB6C1'); // Rosa claro
        }
    }

    // Guardar porcentaje empresa
    $('#btnSavePorcentajeEmpresa').on('click', function() {
        const porcentaje = $('#porcentaje_empresa_input').val();
        $.ajax({
            url: '/api/presupuesto/update-porcentaje-empresa',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                presupuesto_id: presupuestoId,
                porcentaje_empresa: porcentaje
            }),
            success: function(response) {
                if (response.status === 'success') {
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error al guardar el porcentaje');
            }
        });
    });

    // Actualizar resumen al cargar
    actualizarResumen();
    
    // Cargar contadores de gastos vinculados al cargar la página
    function actualizarContadoresGastos() {
        // Obtener todas las facturas del presupuesto
        const presupuestoId = typeof window !== 'undefined' && window.presupuestoId ? window.presupuestoId : (typeof presupuestoId !== 'undefined' ? presupuestoId : null);
        if (!presupuestoId) return;
        
        $.ajax({
            url: '/api/presupuesto/facturas/' + presupuestoId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success' && response.facturas) {
                    response.facturas.forEach(function(factura) {
                        $.ajax({
                            url: '/api/presupuesto/factura/' + factura.id,
                            method: 'GET',
                            success: function(facturaResponse) {
                                if (facturaResponse.status === 'success') {
                                    const count = facturaResponse.gastos ? facturaResponse.gastos.length : 0;
                                    $('#gastos-count-' + factura.id).text(count);
                                }
                            }
                        });
                    });
                }
            }
        });
    }
    
    // Actualizar contadores al cargar
    actualizarContadoresGastos();

    // Subir y procesar factura/boleta
    $('#btnProcessFactura').off('click').on('click', function() {
        // Prevenir múltiples clics
        if ($(this).prop('disabled')) {
            return;
        }
        $(this).prop('disabled', true);
        
        // Limpiar variable global antes de procesar
        window.facturaIdActual = null;
        window.itemsExtraidosFactura = null;
        
        const formData = new FormData($('#formUploadFactura')[0]);
        const usarOcr = $('#factura_usar_ocr').is(':checked');
        
        // Asegurar que el valor de usar_ocr se envíe siempre
        formData.set('usar_ocr', usarOcr ? 'true' : 'false');
        
        $('#uploadFacturaStep1').hide();
        $('#uploadFacturaStep2').show();
        $('#btnProcessFactura').hide();
        $('#btnCancelUpload').prop('disabled', true);
        
        if (usarOcr) {
            $('#procesandoMensaje').text('Extrayendo texto con OCR...');
        } else {
            $('#procesandoMensaje').text('Guardando factura...');
        }
        
        $.ajax({
            url: '/api/presupuesto/upload-factura',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            timeout: 3000000, // 5 minutos (300 segundos) para dar tiempo a Ollama
            success: function(response) {
                if (response.status === 'success') {
                    // Guardar factura_id en variable global
                    window.facturaIdActual = response.factura_id;
                    
                    // Llenar campos del paso 3 con datos extraídos o manuales
                    if (response.factura_data) {
                        $('#factura_numero_documento_step3').val(response.factura_data.numero_documento || '');
                        $('#factura_proveedor_step3').val(response.factura_data.proveedor || '');
                        $('#factura_fecha_emision_step3').val(response.factura_data.fecha_emision || '');
                        $('#factura_neto_step3').val(response.factura_data.neto ? response.factura_data.neto.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                        $('#factura_iva_step3').val(response.factura_data.iva ? response.factura_data.iva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                        $('#factura_total_step3').val(response.factura_data.total ? response.factura_data.total.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                        $('#factura_tipo_documento').val(response.factura_data.tipo_documento || 'factura');
                    }
                    
                    // Los valores ya vienen formateados desde el backend con toLocaleString
                    // No es necesario aplicar formato adicional
                    
                    // Siempre mostrar paso 3 para editar datos antes de confirmar
                    if (response.tiene_items && response.items && response.items.items && response.items.items.length > 0) {
                        // Hay items extraídos, mostrar paso 3 con items editables
                        mostrarItemsExtraidos(response.items, response.texto_extraido);
                        $('#uploadFacturaStep2').hide();
                        $('#uploadFacturaStep3').show();
                        $('#btnConfirmItems').show();
                        $('#btnSaveFacturaFromStep3').hide();
                        $('#btnCancelUpload').prop('disabled', false);
                    } else {
                        // No hay items, mostrar paso 3 solo con datos de factura para editar
                        $('#uploadFacturaStep2').hide();
                        $('#uploadFacturaStep3').show();
                        $('#itemsExtraidosContainer').html('<p class="text-muted">No se encontraron items para extraer. Puedes agregar gastos manualmente después de guardar la factura.</p>');
                        $('#btnConfirmItems').hide();
                        $('#btnSaveFacturaFromStep3').show();
                        $('#btnCancelUpload').prop('disabled', false);
                    }
                } else {
                    alert('Error: ' + response.message);
                    $('#uploadFacturaStep2').hide();
                    $('#uploadFacturaStep1').show();
                    $('#btnProcessFactura').show();
                    $('#btnCancelUpload').prop('disabled', false);
                }
            },
            error: function(xhr) {
                let errorMsg = 'Error al procesar la factura';
                if (xhr.status === 0 || xhr.statusText === 'timeout') {
                    errorMsg = 'Timeout: El procesamiento está tomando más tiempo del esperado. Verifica la conexión con el servidor Ollama o intenta con un documento más pequeño.';
                } else if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                alert(errorMsg);
                $('#uploadFacturaStep2').hide();
                $('#uploadFacturaStep1').show();
                $('#btnProcessFactura').show().prop('disabled', false);
                $('#btnCancelUpload').prop('disabled', false);
                // Limpiar variables globales en caso de error
                window.facturaIdActual = null;
                window.itemsExtraidosFactura = null;
            }
        });
    });

    function mostrarItemsExtraidos(items, textoExtraido) {
        let html = '<table class="table table-bordered table-hover">';
        html += '<thead><tr><th>Descripción</th><th>Cantidad</th><th>Monto Unitario</th><th>Total</th><th>Acción</th></tr></thead>';
        html += '<tbody id="itemsExtraidosTableBody">';
        
        let totalMonto = 0;
        items.items.forEach(function(item, index) {
            const cantidad = Math.round(parseFloat(item.cantidad) || 1);
            const montoUnitario = Math.round(parseFloat(item.monto) || 0);
            const montoTotal = cantidad * montoUnitario;
            totalMonto += montoTotal;
            
            html += `<tr data-item-index="${index}">`;
            html += `<td><input type="text" class="form-control input-sm item-descripcion" value="${(item.descripcion || 'Sin descripción').replace(/"/g, '&quot;')}" data-index="${index}"></td>`;
            html += `<td><input type="text" class="form-control input-sm item-cantidad" value="${cantidad.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}" data-index="${index}" placeholder="1"></td>`;
            html += `<td><input type="text" class="form-control input-sm item-monto" value="${montoUnitario.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}" data-index="${index}" placeholder="0"></td>`;
            html += `<td class="item-total">$ ${montoTotal.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</td>`;
            html += `<td><button class="btn btn-xs btn-danger btn-remove-item" data-index="${index}"><i class="fa fa-trash"></i></button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody>';
        html += `<tfoot><tr><th colspan="3">Total (sin IVA):</th><th id="totalSinIva">$ ${totalMonto.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</th><th></th></tr>`;
        html += `<tr><th colspan="3">IVA (19%):</th><th id="totalIva">$ 0</th><th></th></tr>`;
        html += `<tr><th colspan="3">Total (con IVA):</th><th id="totalConIva">$ ${totalMonto.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</th><th></th></tr></tfoot>`;
        html += '</table>';
        
        if (items.fecha) {
            $('#factura_fecha').val(items.fecha);
        }
        
        $('#itemsExtraidosContainer').html(html);
        
        // Guardar items en variable global
        window.itemsExtraidosFactura = items.items;
        
        // Actualizar totales cuando cambie el tipo de documento
        actualizarTotalesFactura();
        
        // Función para convertir string con punto de miles a número entero
        function parseChileanNumber(str) {
            if (!str) return 0;
            // Eliminar puntos (separador de miles), espacios y cualquier carácter no numérico
            const cleaned = str.toString().replace(/\./g, '').replace(/\s/g, '').replace(/[^0-9]/g, '');
            return Math.round(parseInt(cleaned) || 0);
        }
        
        // Event listeners para editar items
        $(document).off('input blur', '.item-descripcion, .item-cantidad, .item-monto').on('input blur', '.item-descripcion, .item-cantidad, .item-monto', function(e) {
            const index = parseInt($(this).data('index'));
            const row = $(this).closest('tr');
            const $input = $(this);
            
            if ($input.hasClass('item-descripcion')) {
                window.itemsExtraidosFactura[index].descripcion = $input.val();
            } else if ($input.hasClass('item-cantidad')) {
                const valor = parseChileanNumber($input.val());
                window.itemsExtraidosFactura[index].cantidad = valor || 1;
                // Formatear solo cuando pierde el foco o al terminar de escribir
                if (e.type === 'blur' || ($input.val() !== '' && !isNaN(parseChileanNumber($input.val())))) {
                    const cursorPos = $input[0].selectionStart;
                    const oldLength = $input.val().length;
                    $input.val(valor.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
                    // Ajustar posición del cursor
                    if (e.type === 'blur') {
                        $input[0].setSelectionRange(cursorPos, cursorPos);
                    }
                }
            } else if ($input.hasClass('item-monto')) {
                const valor = parseChileanNumber($input.val());
                window.itemsExtraidosFactura[index].monto = valor || 0;
                // Formatear solo cuando pierde el foco o al terminar de escribir
                if (e.type === 'blur' || ($input.val() !== '' && !isNaN(parseChileanNumber($input.val())))) {
                    const cursorPos = $input[0].selectionStart;
                    $input.val(valor.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
                    // Ajustar posición del cursor
                    if (e.type === 'blur') {
                        $input[0].setSelectionRange(cursorPos, cursorPos);
                    }
                }
            }
            
            // Recalcular total de la fila (solo enteros)
            const cantidad = parseChileanNumber(row.find('.item-cantidad').val()) || 1;
            const montoUnitario = parseChileanNumber(row.find('.item-monto').val()) || 0;
            const total = cantidad * montoUnitario;
            row.find('.item-total').text('$ ' + total.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
            
            // Actualizar totales
            actualizarTotalesFactura();
        });
        
        // Event listener para eliminar items
        $(document).off('click', '.btn-remove-item').on('click', '.btn-remove-item', function() {
            const index = $(this).data('index');
            window.itemsExtraidosFactura.splice(index, 1);
            mostrarItemsExtraidos({items: window.itemsExtraidosFactura}, textoExtraido);
        });
    }
    
    // Función para convertir string con punto de miles a número entero
    function parseChileanNumber(str) {
        if (!str) return 0;
        // Eliminar puntos (separador de miles) y espacios
        const cleaned = str.toString().replace(/\./g, '').replace(/\s/g, '');
        return Math.round(parseInt(cleaned) || 0);
    }
    
    function actualizarTotalesFactura() {
        let totalSinIva = 0;
        
        $('#itemsExtraidosTableBody tr').each(function() {
            const cantidad = parseChileanNumber($(this).find('.item-cantidad').val()) || 1;
            const montoUnitario = parseChileanNumber($(this).find('.item-monto').val()) || 0;
            totalSinIva += cantidad * montoUnitario;
        });
        
        const tipoDocumento = $('#factura_tipo_documento').val();
        let iva = 0;
        let totalConIva = totalSinIva;
        
        if (tipoDocumento === 'factura') {
            // Factura: agregar 19% de IVA (redondear a entero)
            iva = Math.round(totalSinIva * 0.19);
            totalConIva = totalSinIva + iva;
        } else {
            // Boleta: el IVA ya está incluido, calcular cuánto es (redondear a entero)
            iva = Math.round(totalSinIva * (19 / 119)); // Si el total incluye IVA, el IVA es 19/119 del total
        }
        
        $('#totalSinIva').text('$ ' + totalSinIva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
        $('#totalIva').text('$ ' + iva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
        $('#totalConIva').text('$ ' + totalConIva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}));
    }
    
    // Actualizar totales cuando cambie el tipo de documento
    $(document).on('change', '#factura_tipo_documento', function() {
        actualizarTotalesFactura();
    });

    // Guardar factura desde paso 3 (sin items)
    $('#btnSaveFacturaFromStep3').off('click').on('click', function() {
        // Prevenir múltiples clics
        if ($(this).prop('disabled')) {
            return;
        }
        $(this).prop('disabled', true);
        
        const facturaId = window.facturaIdActual;
        if (!facturaId) {
            alert('Error: No se encontró ID de factura');
            $(this).prop('disabled', false);
            return;
        }
        
        const formData = {
            tipo_documento: $('#factura_tipo_documento').val(),
            numero_documento: $('#factura_numero_documento_step3').val(),
            proveedor: $('#factura_proveedor_step3').val(),
            fecha_emision: $('#factura_fecha_emision_step3').val() || null,
            neto: parseChileanNumber($('#factura_neto_step3').val()),
            iva: parseChileanNumber($('#factura_iva_step3').val()),
            total: parseChileanNumber($('#factura_total_step3').val())
        };
        
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.status === 'success') {
                    alert('Factura guardada correctamente');
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                    $('#btnSaveFacturaFromStep3').prop('disabled', false);
                }
            },
            error: function(xhr) {
                let errorMsg = 'Error al guardar la factura';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                alert(errorMsg);
                $('#btnSaveFacturaFromStep3').prop('disabled', false);
            }
        });
    });
    
    // Confirmar y agregar items como gastos
    $('#btnConfirmItems').on('click', function() {
        if (!window.itemsExtraidosFactura || window.itemsExtraidosFactura.length === 0) {
            alert('No hay items para agregar');
            return;
        }
        
        const pagadoPorId = $('#factura_pagado_por').val();
        const fecha = $('#factura_fecha').val();
        const tipoDocumento = $('#factura_tipo_documento').val();
        let itemsAgregados = 0;
        let itemsError = 0;
        
        // Agregar cada item como un gasto
        const agregarSiguiente = function(index) {
            if (index >= window.itemsExtraidosFactura.length) {
                if (itemsError === 0) {
                    alert(`Se agregaron ${itemsAgregados} gastos correctamente`);
                    location.reload();
                } else {
                    alert(`Se agregaron ${itemsAgregados} gastos. ${itemsError} tuvieron errores.`);
                    location.reload();
                }
                return;
            }
            
            const item = window.itemsExtraidosFactura[index];
            const cantidad = parseChileanNumber(item.cantidad) || 1;
            const montoUnitario = parseChileanNumber(item.monto) || 0;
            let montoTotal = cantidad * montoUnitario;
            
            // Aplicar lógica de IVA según el tipo de documento
            if (tipoDocumento === 'factura') {
                // Factura: el monto está sin IVA, agregar 19% (redondear a entero)
                montoTotal = Math.round(montoTotal * 1.19);
            } else {
                // Boleta: el monto ya incluye IVA, redondear a entero
                montoTotal = Math.round(montoTotal);
            }
            
            // Actualizar datos de factura antes de guardar items (solo una vez)
            if (index === 0) {
                const facturaId = window.facturaIdActual;
                if (facturaId) {
                    const facturaData = {
                        tipo_documento: $('#factura_tipo_documento').val(),
                        numero_documento: $('#factura_numero_documento_step3').val(),
                        proveedor: $('#factura_proveedor_step3').val(),
                        fecha_emision: $('#factura_fecha_emision_step3').val(),
                        neto: parseChileanNumber($('#factura_neto_step3').val()),
                        iva: parseChileanNumber($('#factura_iva_step3').val()),
                        total: parseChileanNumber($('#factura_total_step3').val())
                    };
                    
                    // Actualizar factura primero (síncrono)
                    $.ajax({
                        url: '/api/presupuesto/factura/' + facturaId,
                        method: 'PUT',
                        contentType: 'application/json',
                        data: JSON.stringify(facturaData),
                        async: false
                    });
                }
            }
            
            const formData = {
                presupuesto_id: presupuestoId,
                descripcion: item.descripcion || 'Item de factura',
                monto: montoTotal, // Ya está redondeado a entero
                tipo: 'materiales',
                pagado_por_id: pagadoPorId || null,
                pagado_por_tipo: 'user',
                fecha: fecha || null,
                factura_id: window.facturaIdActual || null
            };
            
            $.ajax({
                url: '/api/presupuesto/gasto',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(formData),
                success: function(response) {
                    if (response.status === 'success') {
                        itemsAgregados++;
                    } else {
                        itemsError++;
                    }
                    agregarSiguiente(index + 1);
                },
                error: function() {
                    itemsError++;
                    agregarSiguiente(index + 1);
                }
            });
        };
        
        agregarSiguiente(0);
    });

    // Reset modal al cerrar
    $('#modalUploadFactura').on('hidden.bs.modal', function() {
        $('#formUploadFactura')[0].reset();
        $('#factura_usar_ocr').prop('checked', true); // Siempre marcado por defecto
        $('#uploadFacturaStep1').show();
        $('#uploadFacturaStep2').hide();
        $('#uploadFacturaStep3').hide();
        $('#btnConfirmItems').hide();
        $('#btnSaveFacturaFromStep3').hide();
        $('#btnProcessFactura').hide();
        $('#btnCancelUpload').prop('disabled', false);
        window.itemsExtraidosFactura = null;
        window.facturaIdActual = null;
    });
    
    // Mostrar/ocultar campos según estado de OCR
    function toggleCamposManuales() {
        const usarOcr = $('#factura_usar_ocr').is(':checked');
        if (usarOcr) {
            // OCR activo: ocultar campos manuales, mostrar info
            $('#campos_manuales_factura').hide();
            $('#info_ocr_activo').show();
            // Quitar required de campos manuales cuando OCR está activo
            $('#factura_numero_documento, #factura_proveedor, #factura_neto, #factura_iva, #factura_total').removeAttr('required');
        } else {
            // OCR desactivado: mostrar campos manuales, ocultar info
            $('#campos_manuales_factura').show();
            $('#info_ocr_activo').hide();
            // Agregar required a campos manuales cuando OCR está desactivado
            $('#factura_numero_documento, #factura_proveedor, #factura_neto, #factura_iva, #factura_total').attr('required', 'required');
        }
        verificarDatosFactura();
    }
    
    // Mostrar botón procesar si hay archivo o datos
    function verificarDatosFactura() {
        const tieneArchivo = $('#factura_archivo').val() !== '';
        const usarOcr = $('#factura_usar_ocr').is(':checked');
        
        if (usarOcr) {
            // Con OCR: solo necesita archivo
            if (tieneArchivo) {
                $('#btnProcessFactura').show();
            } else {
                $('#btnProcessFactura').hide();
            }
        } else {
            // Sin OCR: necesita todos los campos manuales obligatorios
            const tieneTodosDatos = $('#factura_numero_documento').val() && 
                                   $('#factura_proveedor').val() && 
                                   $('#factura_neto').val() && 
                                   $('#factura_iva').val() && 
                                   $('#factura_total').val();
            if (tieneTodosDatos) {
                $('#btnProcessFactura').show();
            } else {
                $('#btnProcessFactura').hide();
            }
        }
    }
    
    // Event handlers para el modal de factura (usar delegación de eventos para elementos dinámicos)
    $(document).on('change', '#factura_usar_ocr', function() {
        toggleCamposManuales();
    });
    
    $(document).on('input change', '#factura_archivo, #factura_numero_documento, #factura_proveedor, #factura_neto, #factura_iva, #factura_total', function() {
        verificarDatosFactura();
    });
    
    // Procesar automáticamente cuando se selecciona un archivo y OCR está activo
    $(document).on('change', '#factura_archivo', function() {
        const usarOcr = $('#factura_usar_ocr').is(':checked');
        if (usarOcr && $(this).val() !== '') {
            // Esperar un momento para que el usuario vea que se seleccionó el archivo
            setTimeout(function() {
                if ($('#factura_archivo').val() !== '') {
                    $('#btnProcessFactura').click();
                }
            }, 500);
        }
    });
    
    // Inicializar estado cuando se abre el modal
    $('#modalUploadFactura').on('shown.bs.modal', function() {
        $('#factura_usar_ocr').prop('checked', true); // Siempre marcado por defecto
        toggleCamposManuales();
        verificarDatosFactura();
    });
    
    // Editar factura
    $(document).on('click', '.btn-edit-factura', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const facturaId = $(this).data('factura-id');
        if (!facturaId) {
            alert('Error: No se encontró ID de factura');
            return;
        }
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    const factura = response.factura;
                    $('#edit_factura_id').val(factura.id);
                    $('#edit_factura_tipo_documento').val(factura.tipo_documento);
                    $('#edit_factura_numero_documento').val(factura.numero_documento || '');
                    $('#edit_factura_proveedor').val(factura.proveedor || '');
                    $('#edit_factura_fecha_emision').val(factura.fecha_emision || '');
                    $('#edit_factura_neto').val(factura.neto ? factura.neto.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    $('#edit_factura_iva').val(factura.iva ? factura.iva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    $('#edit_factura_total').val(factura.total ? factura.total.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    
                    $('#modalEditFactura').modal('show');
                } else {
                    alert('Error: ' + (response.message || 'No se pudieron cargar los datos'));
                }
            },
            error: function() {
                alert('Error al cargar los datos de la factura');
            }
        });
    });
    
    // Guardar cambios de factura - Asegurar que solo se registre una vez
    $(document).off('click', '#btnSaveFactura').on('click', '#btnSaveFactura', function() {
        // Prevenir múltiples clics
        if ($(this).prop('disabled')) {
            return;
        }
        $(this).prop('disabled', true);
        
        const facturaId = $('#edit_factura_id').val();
        if (!facturaId) {
            alert('Error: ID de factura no encontrado');
            $(this).prop('disabled', false);
            return;
        }
        
        // Función para convertir string con punto de miles a número entero
        function parseChileanNumber(str) {
            if (!str) return 0;
            const cleaned = str.toString().replace(/\./g, '').replace(/\s/g, '');
            return Math.round(parseInt(cleaned) || 0);
        }
        
        const formData = {
            tipo_documento: $('#edit_factura_tipo_documento').val(),
            numero_documento: $('#edit_factura_numero_documento').val(),
            proveedor: $('#edit_factura_proveedor').val(),
            fecha_emision: $('#edit_factura_fecha_emision').val() || null,
            neto: parseChileanNumber($('#edit_factura_neto').val()),
            iva: parseChileanNumber($('#edit_factura_iva').val()),
            total: parseChileanNumber($('#edit_factura_total').val())
        };
        
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.status === 'success') {
                    alert('Factura actualizada correctamente');
                    $('#modalEditFactura').modal('hide');
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                    $('#btnSaveFactura').prop('disabled', false);
                }
            },
            error: function(xhr) {
                let errorMsg = 'Error al actualizar la factura';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                alert(errorMsg);
                $('#btnSaveFactura').prop('disabled', false);
            }
        });
    });
    
    // Eliminar factura - Asegurar que solo se registre una vez
    $(document).off('click', '.btn-delete-factura').on('click', '.btn-delete-factura', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const facturaId = $(this).data('factura-id');
        if (!facturaId) {
            alert('Error: No se encontró ID de factura');
            return;
        }
        
        if (!confirm('¿Está seguro de eliminar esta factura/boleta? Los gastos vinculados se desvincularán automáticamente.')) {
            return;
        }
        
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'DELETE',
            success: function(response) {
                if (response.status === 'success') {
                    alert('Factura eliminada correctamente');
                    location.reload();
                } else {
                    alert('Error: ' + (response.message || 'No se pudo eliminar la factura'));
                }
            },
            error: function() {
                alert('Error al eliminar la factura');
            }
        });
    });
    
    // El campo fecha_emision ya existe en el HTML (factura_fecha_emision_step1)
    // No es necesario agregarlo dinámicamente
});

// ============================================
// HANDLERS DE FACTURAS - FUERA DEL READY
// ============================================
// Registrar handlers inmediatamente, sin esperar document.ready
(function() {
    'use strict';
    
    // Ver detalles de factura
    $(document).on('click', '.btn-view-factura', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const facturaId = $(this).data('factura-id');
        if (!facturaId) {
            alert('Error: No se encontró ID de factura');
            return;
        }
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    const factura = response.factura;
                    const gastos = response.gastos || [];
                    
                    let html = '<div class="row">';
                    html += '<div class="col-md-6"><strong>Tipo:</strong> ' + (factura.tipo_documento === 'factura' ? 'Factura' : 'Boleta') + '</div>';
                    html += '<div class="col-md-6"><strong>Número:</strong> ' + (factura.numero_documento || 'N/A') + '</div>';
                    html += '<div class="col-md-6"><strong>Proveedor:</strong> ' + (factura.proveedor || 'N/A') + '</div>';
                    html += '<div class="col-md-6"><strong>Fecha Emisión:</strong> ' + (factura.fecha_emision || 'N/A') + '</div>';
                    html += '<div class="col-md-4"><strong>Neto:</strong> $ ' + (factura.neto || 0).toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + '</div>';
                    html += '<div class="col-md-4"><strong>IVA:</strong> $ ' + (factura.iva || 0).toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + '</div>';
                    html += '<div class="col-md-4"><strong>Total:</strong> $ ' + (factura.total || 0).toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + '</div>';
                    html += '</div>';
                    
                    if (gastos.length > 0) {
                        html += '<hr><h5>Gastos Vinculados (' + gastos.length + '):</h5>';
                        html += '<table class="table table-bordered">';
                        html += '<thead><tr><th>Descripción</th><th>Monto</th><th>Tipo</th><th>Fecha</th></tr></thead>';
                        html += '<tbody>';
                        gastos.forEach(function(gasto) {
                            html += '<tr>';
                            html += '<td>' + (gasto.descripcion || 'N/A') + '</td>';
                            html += '<td>$ ' + (gasto.monto || 0).toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + '</td>';
                            html += '<td>' + (gasto.tipo || 'N/A') + '</td>';
                            html += '<td>' + (gasto.fecha || 'N/A') + '</td>';
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                    } else {
                        html += '<hr><p class="text-muted">No hay gastos vinculados a esta factura.</p>';
                    }
                    
                    $('#facturaDetailsContent').html(html);
                    $('#modalViewFactura').modal('show');
                } else {
                    alert('Error: ' + (response.message || 'No se pudieron cargar los detalles'));
                }
            },
            error: function() {
                alert('Error al cargar los detalles de la factura');
            }
        });
    });
    
    // Editar factura
    $(document).on('click', '.btn-edit-factura', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const facturaId = $(this).data('factura-id');
        if (!facturaId) {
            alert('Error: No se encontró ID de factura');
            return;
        }
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    const factura = response.factura;
                    $('#edit_factura_id').val(factura.id);
                    $('#edit_factura_tipo_documento').val(factura.tipo_documento || 'factura');
                    $('#edit_factura_numero_documento').val(factura.numero_documento || '');
                    $('#edit_factura_proveedor').val(factura.proveedor || '');
                    $('#edit_factura_fecha_emision').val(factura.fecha_emision || '');
                    $('#edit_factura_neto').val(factura.neto ? factura.neto.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    $('#edit_factura_iva').val(factura.iva ? factura.iva.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    $('#edit_factura_total').val(factura.total ? factura.total.toLocaleString('es-CL', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '');
                    $('#modalEditFactura').modal('show');
                } else {
                    alert('Error: ' + (response.message || 'No se pudieron cargar los datos'));
                }
            },
            error: function() {
                alert('Error al cargar los datos de la factura');
            }
        });
    });
    
    // Guardar cambios de factura
    $(document).on('click', '#btnSaveFactura', function() {
        const facturaId = $('#edit_factura_id').val();
        if (!facturaId) {
            alert('Error: ID de factura no encontrado');
            return;
        }
        
        function parseChileanNumber(str) {
            if (!str) return 0;
            const cleaned = str.toString().replace(/\./g, '').replace(/\s/g, '');
            return Math.round(parseInt(cleaned) || 0);
        }
        
        const formData = {
            tipo_documento: $('#edit_factura_tipo_documento').val(),
            numero_documento: $('#edit_factura_numero_documento').val(),
            proveedor: $('#edit_factura_proveedor').val(),
            fecha_emision: $('#edit_factura_fecha_emision').val(),
            neto: parseChileanNumber($('#edit_factura_neto').val()),
            iva: parseChileanNumber($('#edit_factura_iva').val()),
            total: parseChileanNumber($('#edit_factura_total').val())
        };
        
        $.ajax({
            url: '/api/presupuesto/factura/' + facturaId,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.status === 'success') {
                    alert('Factura actualizada correctamente');
                    $('#modalEditFactura').modal('hide');
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error al actualizar la factura');
            }
        });
    });
    
    // Eliminar factura - Handler ya está registrado arriba en el document.ready
    // No duplicar aquí

    // ========== ACTUALIZACIÓN AUTOMÁTICA DE VERIFICACIÓN DE CÁLCULOS ==========
    
    function actualizarVerificacionCalculos() {
        // Obtener valores del presupuesto
        const $verifContainer = $('[data-presupuesto-descuento]');
        const descuento = parseFloat($verifContainer.data('presupuesto-descuento') || 0);
        const porcentajeEmpresa = parseFloat($verifContainer.data('presupuesto-porcentaje-empresa') || 0);
        
        // 1. Calcular total_items (suma de importe_total de items)
        let totalItems = 0;
        $('#itemsTableBody tr').each(function() {
            const cantidad = parseFloat($(this).find('.cantidad-cell').data('cantidad') || 0);
            const valorUnitario = parseFloat($(this).find('.valor-unitario-cell').data('valor') || 0);
            const importeTotal = cantidad * valorUnitario;
            totalItems += importeTotal;
        });
        
        // 2. Calcular neto
        const descuentoMonto = totalItems * (descuento / 100);
        const neto = totalItems - descuentoMonto;
        
        // 3. Calcular total_gastos (suma de montos de gastos)
        let totalGastos = 0;
        let gastosPagadosEmpresa = 0;
        let gastosPagadosCaja = 0;
        $('#gastosTableBody tr').each(function() {
            const monto = parseFloat($(this).data('monto') || 0);
            const pagadoPorId = $(this).data('pagado-por-id');
            totalGastos += monto;
            if (pagadoPorId === 'empresa') {
                gastosPagadosEmpresa += monto;
            } else if (pagadoPorId === null || pagadoPorId === undefined || pagadoPorId === '') {
                gastosPagadosCaja += monto;
            }
        });
        
        // 4. Calcular utilidad_real
        const utilidadReal = neto - totalGastos;
        
        // 5. Calcular distribución de utilidad
        let totalPorcentajeEmpleados = 0;
        let totalUtilidadEmpleados = 0;
        let totalPagosEmpleadosFinal = 0;
        let anticiposEmpresa = 0;
        let anticiposPagadosCaja = 0;
        const anticiposADevolver = {};
        
        $('.pago-empleado-card').each(function() {
            const porcentajePago = parseFloat($(this).data('porcentaje-pago') || 0);
            const anticipo = parseFloat($(this).data('anticipo') || 0);
            const quienPagoAnticipoId = $(this).data('quien-pago-anticipo-id');
            const gastosPagados = parseFloat($(this).data('gastos-pagados') || 0);
            
            totalPorcentajeEmpleados += porcentajePago;
            
            // Utilidad del empleado
            const utilidadEmpleado = Math.round(utilidadReal * (porcentajePago / 100));
            totalUtilidadEmpleados += utilidadEmpleado;
            
            // Reembolso del empleado = gastos pagados por el empleado
            const reembolsoEmpleado = gastosPagados;
            
            // Pago total empleado = utilidad + reembolso - anticipo
            const pagoTotal = utilidadEmpleado + reembolsoEmpleado - anticipo;
            totalPagosEmpleadosFinal += pagoTotal;
            
            // Manejar anticipos
            if (anticipo > 0) {
                if (quienPagoAnticipoId === 'empresa' || quienPagoAnticipoId === -1) {
                    anticiposEmpresa += anticipo;
                } else if (quienPagoAnticipoId === null || quienPagoAnticipoId === undefined || quienPagoAnticipoId === '') {
                    anticiposPagadosCaja += anticipo;
                } else {
                    // Anticipo pagado por otro empleado
                    const empleadoId = parseInt(quienPagoAnticipoId);
                    if (empleadoId > 0) {
                        if (!anticiposADevolver[empleadoId]) {
                            anticiposADevolver[empleadoId] = 0;
                        }
                        anticiposADevolver[empleadoId] += anticipo;
                    }
                }
            }
        });
        
        // Utilidad empresa
        const utilidadEmpresa = Math.round(utilidadReal * (porcentajeEmpresa / 100));
        
        // Aplicar delta de redondeo
        const utilidadDistribuida = utilidadEmpresa + totalUtilidadEmpleados;
        const deltaUtilidad = utilidadReal - utilidadDistribuida;
        if (Math.abs(deltaUtilidad) > 0.01) {
            totalUtilidadEmpleados += deltaUtilidad;
        }
        
        // Reembolso empresa
        const reembolsoEmpresa = gastosPagadosEmpresa;
        
        // Recibe empresa
        const recibeEmpresa = utilidadEmpresa + reembolsoEmpresa + anticiposEmpresa;
        
        // Total porcentaje distribución
        const totalPorcentajeDistribucion = totalPorcentajeEmpleados + porcentajeEmpresa;
        
        // Total anticipos a devolver
        const totalAnticiposADevolver = Object.values(anticiposADevolver).reduce((sum, val) => sum + val, 0);
        
        // Verificaciones
        const verificacionNetoValor = utilidadReal + totalGastos;
        const verificacionNetoOk = Math.abs(verificacionNetoValor - neto) < 0.01;
        const verificacionUtilidadOk = Math.abs(utilidadReal - utilidadDistribuida) < 0.01;
        const netoCheck = recibeEmpresa + totalPagosEmpleadosFinal + gastosPagadosCaja + anticiposPagadosCaja;
        const verificacionFinalOk = Math.abs(neto - netoCheck) < 0.01;
        const diferenciaVerificacionNeto = neto - netoCheck;
        const verificacionPorcentajesOk = Math.abs(totalPorcentajeDistribucion - 100) < 0.01;
        
        // Actualizar elementos HTML
        function formatNumber(num) {
            return num.toLocaleString('es-CL', {maximumFractionDigits: 0});
        }
        
        function formatPercent(num) {
            return num.toFixed(2);
        }
        
        $('#verif_neto').text('$ ' + formatNumber(neto));
        $('#verif_utilidad_real').text('$ ' + formatNumber(utilidadReal));
        $('#verif_total_gastos').text('$ ' + formatNumber(totalGastos));
        $('#verif_neto_valor').text('$ ' + formatNumber(verificacionNetoValor));
        $('#verif_icon_neto').removeClass('fa-check fa-times').addClass(verificacionNetoOk ? 'fa-check' : 'fa-times');
        
        $('#verif_porcentaje_empleados').text(formatPercent(totalPorcentajeEmpleados) + '%');
        $('#verif_porcentaje_empresa').text(formatPercent(porcentajeEmpresa) + '%');
        $('#verif_total_porcentaje_distribucion').text(formatPercent(totalPorcentajeDistribucion) + '%')
            .css('color', verificacionPorcentajesOk ? '#90EE90' : '#FFB6C1');
        $('#verif_utilidad_distribuida').text('$ ' + formatNumber(utilidadDistribuida));
        $('#verif_icon_utilidad').removeClass('fa-check fa-times').addClass(verificacionUtilidadOk ? 'fa-check' : 'fa-times');
        
        $('#verif_total_pagos_empleados').text('$ ' + formatNumber(totalPagosEmpleadosFinal));
        $('#verif_diferencia').text('$ ' + formatNumber(recibeEmpresa));
        if (totalAnticiposADevolver > 0) {
            $('#verif_anticipos_a_devolver').show();
            $('#verif_anticipos_a_devolver_valor').text('$ ' + formatNumber(totalAnticiposADevolver));
        } else {
            $('#verif_anticipos_a_devolver').hide();
        }
        
        $('#verif_distribucion_utilidad_real').text('$ ' + formatNumber(utilidadReal))
            .css('color', verificacionUtilidadOk ? '#90EE90' : '#FFB6C1');
        $('#verif_suma_total_neto').text('$ ' + formatNumber(neto))
            .css('color', verificacionFinalOk ? '#90EE90' : '#FFB6C1');
        
        // Mensaje de verificación final
        const $iconFinal = $('#verif_icon_final');
        const $mensajeFinal = $('#verif_mensaje_final');
        $iconFinal.removeClass('fa-check fa-times').addClass(verificacionFinalOk ? 'fa-check' : 'fa-times');
        if (verificacionFinalOk) {
            $mensajeFinal.html('<span style="color: #90EE90;">✓ Los cálculos están cuadrados (Neto = Recibe Empresa + Pagos Empleados + Gastos Caja + Anticipos Caja)</span>');
        } else {
            $mensajeFinal.html('<span style="color: #FFB6C1;">✗ Los cálculos NO cuadran (Diferencia: $ ' + formatNumber(diferenciaVerificacionNeto) + ')</span>');
        }
        
        // Desglose
        if (gastosPagadosCaja > 0 || anticiposPagadosCaja > 0) {
            let desgloseTexto = 'Recibe Empresa ($ ' + formatNumber(recibeEmpresa) + ') + Pagos Empleados ($ ' + formatNumber(totalPagosEmpleadosFinal) + ')';
            if (gastosPagadosCaja > 0) {
                desgloseTexto += ' + Gastos Caja ($ ' + formatNumber(gastosPagadosCaja) + ')';
            }
            if (anticiposPagadosCaja > 0) {
                desgloseTexto += ' + Anticipos Caja ($ ' + formatNumber(anticiposPagadosCaja) + ')';
            }
            desgloseTexto += ' = $ ' + formatNumber(netoCheck);
            $('#verif_desglose').show();
            $('#verif_desglose_texto').text(desgloseTexto);
        } else {
            $('#verif_desglose').hide();
        }
        
        // Actualizar también los valores de IVA
        actualizarIVA();
    }
    
    // Función para actualizar valores de IVA
    function actualizarIVA() {
        // Calcular IVA Crédito (suma de IVA de todas las facturas)
        let ivaCredito = 0;
        $('#facturasTableBody tr').each(function() {
            const iva = parseFloat($(this).data('factura-iva') || 0);
            ivaCredito += iva;
        });
        
        // Calcular IVA Compra (IVA del presupuesto)
        const $verifContainer = $('[data-presupuesto-descuento]');
        const ivaPorcentaje = parseFloat($verifContainer.data('presupuesto-iva') || 19);
        
        // Calcular total_items
        let totalItems = 0;
        $('#itemsTableBody tr').each(function() {
            const cantidad = parseFloat($(this).find('.cantidad-cell').data('cantidad') || 0);
            const valorUnitario = parseFloat($(this).find('.valor-unitario-cell').data('valor') || 0);
            const importeTotal = cantidad * valorUnitario;
            totalItems += importeTotal;
        });
        
        // Calcular neto
        const descuento = parseFloat($verifContainer.data('presupuesto-descuento') || 0);
        const descuentoMonto = totalItems * (descuento / 100);
        const neto = totalItems - descuentoMonto;
        
        // Calcular IVA Compra
        const ivaCompra = Math.round(neto * (ivaPorcentaje / 100));
        
        // Calcular IVA a pagar
        const ivaAPagar = ivaCompra - ivaCredito;
        
        // Actualizar elementos HTML
        function formatNumber(num) {
            return num.toLocaleString('es-CL', {maximumFractionDigits: 0});
        }
        
        $('#iva_credito').text('$ ' + formatNumber(ivaCredito));
        $('#iva_compra').text('$ ' + formatNumber(ivaCompra));
        $('#iva_a_pagar').text('$ ' + formatNumber(ivaAPagar));
        
        const $diferenciaIva = $('#diferencia_iva');
        $diferenciaIva.text('$ ' + formatNumber(ivaAPagar));
        $diferenciaIva.css('color', ivaAPagar >= 0 ? '#FFB6C1' : '#90EE90');
        
        // Actualizar mensaje de diferencia IVA
        const $mensajeDiferencia = $diferenciaIva.closest('.col-md-6').find('p:last');
        if (ivaAPagar >= 0) {
            $mensajeDiferencia.html('<i class="fa fa-exclamation-triangle"></i> <span style="color: #FFB6C1;">Debe pagar IVA</span>');
        } else {
            $mensajeDiferencia.html('<i class="fa fa-check-circle"></i> <span style="color: #90EE90;">Crédito IVA a favor</span>');
        }
    }
    
    // Llamar a actualizarVerificacionCalculos y actualizarIVA cuando se cargue la página
    $(document).ready(function() {
        // Pequeño delay para asegurar que todos los elementos estén cargados
        setTimeout(function() {
            actualizarVerificacionCalculos();
            actualizarIVA();
        }, 100);
    });
    
    // Actualizar IVA cuando se modifiquen items (afecta IVA compra)
    // La función se llama automáticamente después de actualizarVerificacionCalculos
    // ya que ambos dependen de los mismos datos
    
    // ========== GESTIÓN DE ITEMS DEL PRESUPUESTO ==========
    
    // Agregar item
    $(document).off('click', '#btnAgregarItem').on('click', '#btnAgregarItem', function() {
        $('#modalItemPresupuestoLabel').text('Agregar Item');
        $('#formItemPresupuesto')[0].reset();
        $('#item_id').val('');
        $('#item_cantidad').val(1);
        $('#item_valor_unitario').val(0);
        $('#item_tipo').val('Material');
        $('#itemMsg').html('');
        $('#modalItemPresupuesto').modal('show');
    });
    
    // Editar item
    $(document).off('click', '.btn-edit-item').on('click', '.btn-edit-item', function() {
        const itemId = $(this).data('item-id');
        const $row = $('tr[data-item-id="' + itemId + '"]');
        
        if ($row.length === 0) {
            alert('No se encontró el item');
            return;
        }
        
        $('#modalItemPresupuestoLabel').text('Editar Item');
        $('#item_id').val(itemId);
        $('#item_referencia').val($row.find('td:eq(0)').text().trim());
        $('#item_cantidad').val($row.find('.cantidad-cell').data('cantidad') || $row.find('td:eq(1)').text().trim());
        $('#item_ubicacion').val($row.find('td:eq(2)').text().trim());
        $('#item_tipologia').val($row.find('td:eq(3)').text().trim());
        
        // Obtener valor unitario desde el atributo data
        const valorUnitario = $row.find('.valor-unitario-cell').data('valor') || 
                             parseFloat($row.find('.valor-unitario-cell').text().replace(/[^0-9.-]/g, '')) || 0;
        $('#item_valor_unitario').val(valorUnitario);
        
        // Intentar obtener tipo y características desde la base de datos mediante AJAX
        $.ajax({
            url: '/api/presupuesto/item/' + itemId,
            method: 'GET',
            success: function(response) {
                if (response.status === 'success' && response.item) {
                    $('#item_tipo').val(response.item.tipo || 'Material');
                    $('#item_caracteristicas').val(response.item.caracteristicas || '');
                }
            },
            error: function() {
                // Si falla, usar valores por defecto
                $('#item_tipo').val('Material');
                $('#item_caracteristicas').val('');
            }
        });
        
        $('#itemMsg').html('');
        $('#modalItemPresupuesto').modal('show');
    });
    
    // Eliminar item
    $(document).off('click', '.btn-delete-item').on('click', '.btn-delete-item', function() {
        if (!confirm('¿Estás seguro de eliminar este item?')) return;
        
        const itemId = $(this).data('item-id');
        
        $.ajax({
            url: '/delete_presupuesto_item/' + itemId,
            type: 'POST',
            success: function(response) {
                if (response.status === 'success') {
                    $('tr[data-item-id="' + itemId + '"]').remove();
                    if ($('#itemsTableBody tr').length === 0) {
                        $('#itemsTableBody').html('<tr><td colspan="15" class="text-center text-muted">No hay items en el presupuesto</td></tr>');
                    }
                    alert('Item eliminado correctamente');
                    location.reload(); // Recargar para actualizar totales
                } else {
                    alert(response.message || 'Error al eliminar item');
                }
            },
            error: function() {
                alert('Error al eliminar item');
            }
        });
    });
    
    // Guardar item (agregar o editar)
    $(document).off('submit', '#formItemPresupuesto').on('submit', '#formItemPresupuesto', function(e) {
        e.preventDefault();
        const $form = $(this);
        const $msg = $('#itemMsg');
        const itemId = $('#item_id').val();
        const url = itemId ? '/update_presupuesto_item/' + itemId : '/add_presupuesto_item';
        
        $msg.html('');
        
        $.ajax({
            url: url,
            type: 'POST',
            data: $form.serialize(),
            success: function(response) {
                if (response.status === 'success') {
                    $msg.html('<div class="alert alert-success">' + response.message + '</div>');
                    setTimeout(function() {
                        $('#modalItemPresupuesto').modal('hide');
                        location.reload();
                    }, 500);
                } else {
                    $msg.html('<div class="alert alert-danger">' + response.message + '</div>');
                }
            },
            error: function(xhr) {
                let errorMsg = 'Error al guardar item';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                $msg.html('<div class="alert alert-danger">' + errorMsg + '</div>');
            }
        });
    });
})();


