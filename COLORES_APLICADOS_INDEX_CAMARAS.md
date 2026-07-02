# 🎨 Colores Aplicados en index_camaras.html

## Guía de Verificación Visual

Este documento lista todos los colores de la paleta aplicados y dónde puedes verlos en la página `index_camaras.html`.

---

## 📍 **1. SIDEBAR (Barra lateral izquierda)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--sidebar-bg-open` | `rgba(15, 23, 42, 0.25)` | Barra lateral completa | `.sidebar` |
| `--sidebar-border` | `rgba(148, 163, 184, 0.1)` | Borde derecho de la sidebar | `.sidebar` border-right |
| `--sidebar-text` | `#E2E8F0` | Texto de los enlaces | `.sidebar-link` |
| `--sidebar-text-hover` | `#FFFFFF` | Texto al pasar el mouse | `.sidebar-link:hover` |
| `--sidebar-active` | `#0066FF` | Enlace activo | `.sidebar-link.active` |
| `--sidebar-border` | `rgba(64, 224, 208, 0.3)` | Borde del header | `.sidebar-header` border-bottom |
| `--primary-50` | `rgba(64, 224, 208, 0.1)` | Fondo del footer | `.sidebar-footer` |

**Ubicación Visual:** Barra lateral izquierda de la página

---

## 📍 **2. HERO SECTION (Sección principal al inicio)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--gradient-hero` | `linear-gradient(135deg, rgba(0, 102, 255, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%)` | Fondo de la sección hero | `.hero` background |
| `--text-inverse` | `#FFFFFF` | Título "NexSecure" | `.hero-title` |
| `--neutral-200` | `#E2E8F0` | Subtítulo descriptivo | `.hero-subtitle` |
| `--hero-overlay` | `rgba(0, 0, 0, 0.4)` | Overlay oscuro sobre el fondo | `.hero .overlay` |
| `rgba(0, 102, 255, 0.33)` | Glow azul detrás del logo | Efecto de brillo | `.hero::after` |

**Ubicación Visual:** Primera sección grande con el logo y título "NexSecure - Soluciones de Seguridad"

**Botón "Ver soluciones":**
- Fondo: `#FFFFFF` (blanco)
- Texto: `var(--primary)` = `#0066FF` (azul)
- Sombra: `var(--shadow-md)`

---

## 📍 **3. SERVICES SECTION (Sección de Servicios)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--text-primary` | `#0F172A` | Títulos de servicios | `.service-item .title` |
| `--primary` | `#0066FF` | Enlaces de servicios al hover | `.service-item .title a:hover` |
| `--shadow-md` | `0 4px 6px rgba(0, 102, 255, 0.1)` | Sombra al hover en items | `.service-item-clickable:hover` |

**Ubicación Visual:** Sección con lista de servicios (Videovigilancia, Cercos, Domótica, etc.)

---

## 📍 **4. CALL TO ACTION BAND (Banda de llamada a la acción)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-dark-secondary` | `#1E293B` | Fondo de la banda | `.call-to-action-band` |
| `rgba(0, 212, 255, 0.1)` | Bordes superior e inferior | `.call-to-action-band` border-top/bottom |
| `--gradient-turquoise` | `linear-gradient(90deg, #00d4ff 0%, #0099cc 100%)` | Título "¿Listo para proteger..." | `.cta-band-title` (texto con gradiente) |
| `--neutral-200` | `#E2E8F0` | Texto descriptivo | `.cta-band-desc` |
| `--accent-turquoise` | `#00D4FF` | Texto destacado "¡Cotiza sin compromiso!" | `.cta-band-highlight` |
| `--gradient-turquoise` | `linear-gradient(90deg, #0099cc 0%, #00d4ff 100%)` | Botón "¡Cotiza ahora!" | `.cta-band-btn` background |
| `--text-inverse` | `#FFFFFF` | Texto del botón | `.cta-band-btn` color |
| `--shadow-primary-glow` | `0 4px 32px rgba(0, 212, 255, 0.4)` | Sombra del botón al hover | `.cta-band-btn:hover` |

**Ubicación Visual:** Banda horizontal azul oscura con el texto "¿Listo para proteger y optimizar tu hogar o empresa?"

---

## 📍 **5. ABOUT SECTION (Sección Nosotros)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-primary` | `#FFFFFF` | Fondo de la sección | `#about` section |
| `--gradient-sky` | `linear-gradient(90deg, #00c6fb 0%, #005bea 100%)` | Título "¡Nosotros!" | `.about-title-gradient` |
| `--accent-turquoise-dark` | `#0099CC` | Texto de logros | `.about-achievements` |

**Ubicación Visual:** Sección con el título "¡Nosotros!" y la información de misión, visión y valores

---

## 📍 **6. CLIENTS SECTION (Sección de Clientes)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-primary` | `#FFFFFF` | Fondo de la sección | `#clients` section |
| `--gradient-sky` | `linear-gradient(90deg, #00c6fb 0%, #005bea 100%)` | Título "Confían en Nosotros" | `.about-title-gradient` |

**Ubicación Visual:** Sección con logos de clientes (BHG, La Ropa Americana, etc.)

---

## 📍 **7. PORTFOLIO/GALLERY SECTION (Galería)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--primary` | `#0066FF` | Botones de filtro activos | `.portfolio-filters li.filter-active` |
| `--text-inverse` | `#FFFFFF` | Texto de filtros activos | `.portfolio-filters li.filter-active` |
| `--primary` | `#0066FF` | Enlaces de preview/details | `.portfolio-info .preview-link:hover` |

**Ubicación Visual:** Sección con galería de imágenes de proyectos (filtros: Todos, Videovigilancia, Alarmas, etc.)

---

## 📍 **8. FAQ SECTION (Preguntas Frecuentes)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-primary` | `#FFFFFF` | Fondo de la sección | `#faq` section |
| `--gradient-turquoise` | `linear-gradient(90deg, #00d4ff 0%, #0099cc 100%)` | Título "Preguntas Frecuentes" | `.section-title-blue` |
| `--neutral-800` | `#1E293B` | Iconos de flecha en preguntas | `.faq-toggle-icon` SVG stroke |
| `--primary` | `#0066FF` | Texto de pregunta al hover | `.faq-question:hover` |

**Ubicación Visual:** Sección con tarjetas de preguntas frecuentes (6 tarjetas en grid)

---

## 📍 **9. CONTACT SECTION (Contacto)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--primary` | `#0066FF` | Iconos de información | `.contact .info-item i` |
| `--primary` | `#0066FF` | Botón "Send Message" | `.contact .php-email-form button[type=submit]` |
| `--primary` | `#0066FF` | Borde de inputs al focus | `.contact .php-email-form input:focus` |

**Ubicación Visual:** Sección final con mapa y formulario de contacto

---

## 📍 **10. FOOTER (Pie de página)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-dark` | `#0F172A` | Fondo principal del footer | `.footer` |
| `--bg-dark-secondary` | `#1E293B` | Fondo secundario | Gradiente del footer |
| `--primary` | `#0066FF` | Iconos de enlaces | `.footer .footer-links ul i` |
| `--primary` | `#0066FF` | Enlaces al hover | `.footer .footer-links ul a:hover` |
| `--primary` | `#0066FF` | Botón de newsletter | `.footer .footer-newsletter .newsletter-form input[type=submit]` |

**Ubicación Visual:** Pie de página oscuro con información de contacto y enlaces

---

## 📍 **11. MODAL DE PRESUPUESTO**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--bg-overlay` | `rgba(15, 23, 42, 0.8)` | Fondo oscuro del modal | `.presupuesto-modal-overlay` |
| `--primary-800` | `#002966` | Fondo de las tarjetas del wizard | `.wizard-card` |
| `--text-inverse` | `#FFFFFF` | Títulos dentro del modal | `h5` dentro del modal |
| `--primary-700` | `#003D99` | Iconos SVG de las tarjetas de servicio | `.card-image svg` stroke |
| `--primary` | `#0066FF` | Bordes de las tarjetas | `.card` border |
| `--primary` | `#0066FF` | Tarjetas seleccionadas | `.card.selected` |
| `--shadow-xl` | `0 20px 25px rgba(0, 102, 255, 0.2)` | Sombra de las tarjetas | `.wizard-card` |

**Ubicación Visual:** Modal que se abre al hacer clic en "Presupuestos" o botones de cotización

**Paso 3 del Modal (Formulario):**
- Fondo de cajas: `var(--primary-800)` = `#002966`
- Texto: `var(--text-inverse)` = `#FFFFFF`
- Botones: `var(--btn-primary)` = `#0066FF`

---

## 📍 **12. MODAL DE SERVICIO DETALLE**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--gradient-primary` | `linear-gradient(135deg, #0066FF 0%, #0052CC 100%)` | Header del modal | `#modalServicio .modal-header` |
| `--text-inverse` | `#FFFFFF` | Título del modal | `#modalServicio .modal-title` |
| `--neutral-50` | `#F8FAFC` | Fondo de items de lista | `#modalServicioList li` |
| `--neutral-200` | `#E2E8F0` | Fondo al hover | `#modalServicioList li:hover` |
| `--primary` | `#0066FF` | Borde izquierdo al hover | `#modalServicioList li:hover` border-left |
| `--primary-50` | `#E6F0FF` | Fondo de item activo | `#modalServicioList li.active` |
| `--primary` | `#0066FF` | Iconos de la lista | `#modalServicioList li i` |
| `--primary` | `#0066FF` | Checkbox seleccionado | `#modalServicioList li .service-checkbox:checked` |
| `--text-secondary` | `#475569` | Texto de detalles expandidos | `#modalServicioList li .item-details` |
| `--neutral-300` | `#CBD5E1` | Borde superior de detalles | `#modalServicioList li .item-details` border-top |
| `--shadow-md` | `0 4px 6px rgba(0, 102, 255, 0.1)` | Sombra del modal | `#modalServicio .modal-content` |
| `--shadow-primary` | `0 4px 20px rgba(0, 102, 255, 0.3)` | Sombra de items activos | `#modalServicioList li.active` |

**Ubicación Visual:** Modal que se abre al hacer clic en cualquier servicio (ej: "Sistemas de Videovigilancia")

---

## 📍 **13. SCROLL TOP BUTTON (Botón para subir)**

### Colores Aplicados:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--neutral-800` | `#1E293B` | Fondo del botón | `.scroll-top` |
| `--text-inverse` | `#FFFFFF` | Color del icono | `.scroll-top i` |
| `--neutral-900` | `#0F172A` | Fondo al hover | `.scroll-top:hover` |
| `--shadow-lg` | `0 10px 15px rgba(0, 102, 255, 0.15)` | Sombra base | `.scroll-top` |
| `--shadow-xl` | `0 6px 32px rgba(0, 0, 0, 0.2)` | Sombra al hover | `.scroll-top:hover` |

**Ubicación Visual:** Botón circular en la esquina inferior derecha para volver arriba

---

## 📍 **14. BOTONES GENERALES**

### Botón Primario:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--btn-primary` / `--primary` | `#0066FF` | Fondo del botón | `.btn-primary` |
| `--btn-primary-text` / `--text-inverse` | `#FFFFFF` | Texto del botón | `.btn-primary` |
| `--btn-primary-hover` / `--primary-600` | `#0052CC` | Fondo al hover | `.btn-primary:hover` |

**Ubicación Visual:** 
- Botón "Ver soluciones" en el hero
- Botón "Solicitar Presupuesto por WhatsApp" en modales
- Botones "Siguiente", "Enviar solicitud" en el modal de presupuesto

### Botón Secundario:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--btn-secondary` / `--neutral-500` | `#64748B` | Fondo del botón | `.btn-secondary` |
| `--btn-secondary-text` / `--text-inverse` | `#FFFFFF` | Texto del botón | `.btn-secondary` |

**Ubicación Visual:** 
- Botones "Anterior" en el modal de presupuesto
- Botón "Cerrar" en modales

---

## 📍 **15. ELEMENTOS ESPECÍFICOS**

### Títulos de Sección:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--gradient-sky` | `linear-gradient(90deg, #00c6fb 0%, #005bea 100%)` | Títulos principales | `.section-title h2`, `.about-title-gradient` |
| `--gradient-turquoise` | `linear-gradient(90deg, #00d4ff 0%, #0099cc 100%)` | Título "Preguntas Frecuentes" | `.section-title-blue` |

**Ubicación Visual:** Títulos grandes de cada sección

### Iconos:

| Variable CSS | Color | Dónde Verlo | Elemento |
|--------------|-------|-------------|----------|
| `--primary` | `#0066FF` | Iconos de servicios | `.service-item .icon i` |
| `--primary` | `#0066FF` | Iconos en modales | `#modalServicioList li i` |
| `--primary-700` | `#003D99` | Iconos SVG en tarjetas | `.card-image svg` stroke |

---

## 🎯 **RESUMEN POR COLOR PRINCIPAL**

### **#0066FF (Azul Principal)**
- ✅ Botones primarios
- ✅ Enlaces y hover
- ✅ Bordes de elementos activos
- ✅ Iconos
- ✅ Títulos con gradiente
- ✅ Elementos seleccionados

### **#00D4FF (Turquesa)**
- ✅ Títulos de CTA
- ✅ Textos destacados
- ✅ Gradientes de acento
- ✅ Bordes de elementos especiales

### **#0099CC (Turquesa Oscuro)**
- ✅ Hover de elementos turquesa
- ✅ Textos de logros
- ✅ Gradientes reversos

### **#00C6FB (Sky Blue)**
- ✅ Títulos principales de secciones
- ✅ Gradientes de títulos

---

## 🔍 **CÓMO VERIFICAR LOS CAMBIOS**

1. **Abre la página** `index_camaras.html` en tu navegador
2. **Inspecciona elementos** con F12 (DevTools)
3. **Busca las variables CSS** en la pestaña "Computed" o "Styles"
4. **Verifica visualmente** cada sección según la tabla anterior

### **Herramientas de Verificación:**

1. **Chrome DevTools:**
   - F12 → Elements → Selecciona elemento → Styles
   - Busca `var(--primary)`, `var(--accent-turquoise)`, etc.

2. **Verificación Visual:**
   - Sidebar: Barra izquierda
   - Hero: Primera sección grande
   - CTA Band: Banda azul oscura
   - Modales: Abre "Presupuestos" o cualquier servicio

---

## 📝 **NOTAS IMPORTANTES**

- Todos los colores ahora usan **variables CSS** de `color-palette.css`
- Si cambias un color en la paleta, se actualizará en toda la página
- Los colores tienen **valores de fallback** (ej: `var(--primary, #0066FF)`) por si la paleta no carga
- Algunos colores pueden verse ligeramente diferentes debido a transparencias y efectos de blur

---

## 🚀 **PRÓXIMOS PASOS**

Si quieres ajustar algún color:
1. Edita `static/css/color-palette.css`
2. Cambia el valor de la variable correspondiente
3. Recarga la página para ver los cambios

