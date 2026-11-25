const $ = id => document.getElementById(id);
const money = value => new Intl.NumberFormat('es-CO', {style:'currency',currency:'COP',maximumFractionDigits:0}).format(value || 0);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fecha = value => new Date(value).toLocaleTimeString('es-CO', {hour:'2-digit',minute:'2-digit'});
const normalizar = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
const nombres = ['Valentina Rojas','Laura Castaño','Andrés Molina','Mateo Salazar','Daniela Ruiz','Santiago Vélez'];
const estados = {'recibido':'Recibido','en preparación':'En cocina','listo':'Listo','en ruta':'En ruta','entregado':'Entregado','cancelado':'Cancelado'};
const siguiente = {'recibido':'en preparación','en preparación':'listo','listo':'en ruta','en ruta':'entregado'};
let ctx;
let restaurantes = [];
let busqueda = '';
let categoria = '';
let soloAbiertos = false;
let favoritosFiltro = false;
let actualizando = false;
let ultimaConsulta = 0;
let firmaResumen = '';
let firmaRecientes = '';
let pedidosPlataforma=[];
let ultimoPedido=0;
let firmaPedidos='';
let favoritos;
try { favoritos = new Set(JSON.parse(localStorage.getItem('parche.favoritos') || '[]')); } catch { favoritos = new Set(); }

function boton(texto, callback, clase = 'primary') {
 const el = document.createElement('button');
 el.type = 'button';
 el.className = clase;
 el.textContent = texto;
 el.onclick = callback;
 return el;
}

function etiqueta(estado) {
 return `<span class="status-chip status-${esc(estado.replaceAll(' ','-'))}"><i></i>${esc(estados[estado] || (estado === 'abierto' ? 'Abierta' : 'Pausada'))}</span>`;
}

function foto(url, alt, clase = '') {
 const img = document.createElement('img');
 img.src = url;
 img.alt = alt;
 img.className = clase;
 img.loading = 'lazy';
 img.decoding = 'async';
 return img;
}

function mensajeError(error) { ctx.notify(error.message || 'No se pudo completar la operación.', true); }

export function configurar(contexto) {
 ctx = contexto;
 $('modal').addEventListener('close', () => $('modal').classList.remove('restaurant-modal'));
}

export async function resumen(contenedor) {
 if (!contenedor.querySelector('.platform-summary')) {
  contenedor.innerHTML = `<div class="platform-summary"><section class="welcome-panel"><div class="welcome-copy"><span class="eyebrow">BUEN SABOR. BUEN EQUIPO.</span><h2>Todo el parche,<br>en movimiento.</h2><p>Tus cocinas, sus sabores y cada pedido.<br>Una vista para seguirles el ritmo.</p><div class="welcome-action"></div></div><div class="welcome-visual"><img src="/media/hamburguesas_1568901346375-23c9450c58cd.jpg" alt="Hamburguesa artesanal con vegetales"><span class="photo-caption">El antojo también entra por los ojos.</span></div><span class="simulation-pill">Simulación de plataforma</span></section><div class="platform-stats"><article class="metric-card glass"><span class="metric-icon coral">⌂</span><span class="label">Cocinas en el parche</span><strong data-metric="restaurantes">—</strong><small data-metric-note="abiertos">Consultando actividad</small></article><article class="metric-card glass"><span class="metric-icon gold">↗︎</span><span class="label">Pedidos en movimiento</span><strong data-metric="activos">—</strong><small>Recibidos, en cocina o en ruta</small></article><article class="metric-card glass"><span class="metric-icon sage">$</span><span class="label">Ventas simuladas de hoy</span><strong data-metric="ventas_hoy">—</strong><small>Solo pedidos entregados</small></article><article class="metric-card glass"><span class="metric-icon plum">≡</span><span class="label">Platos para elegir</span><strong data-metric="productos">—</strong><small>Diez especialidades distintas</small></article></div><div class="platform-columns"><section class="panel glass"><div class="panel-header"><div><span class="eyebrow">CÓMO VA LA SEMANA</span><h2>Sabor que se mueve</h2><p class="muted">Ventas simuladas de los últimos siete días.</p></div><span class="chart-period">7 días</span></div><div class="sales-chart" id="sales-chart"></div><div class="chart-foot"><span>Historial de demostración</span><b id="week-total"></b></div></section><section class="panel glass"><div class="panel-header"><div><span class="eyebrow">LOS MÁS PEDIDOS</span><h2>Favoritos del parche</h2></div></div><div id="top-restaurants" class="top-restaurants"></div></section></div><section class="panel glass"><div class="panel-header"><div><span class="eyebrow">EN VIVO, SIN PERDER EL RITMO</span><h2>Últimos pedidos</h2><p class="muted">Clientes, cocinas y entregas de la simulación.</p></div><span class="live-caption"><i class="dot"></i> Actualización automática</span></div><div class="table-wrap"><table class="platform-orders"><thead><tr><th>Pedido</th><th>Cocina</th><th>Cliente</th><th>Estado</th><th>Total</th><th>Hora</th><th></th></tr></thead><tbody id="platform-orders"></tbody></table></div></section><p class="simulation-note">Los negocios, menús y pedidos son ficticios. Las fotografías son referencias de presentación.</p></div>`;
  contenedor.querySelector('.welcome-action').append(boton('Explorar restaurantes  ↗︎', () => ctx.go('restaurantes')));
  firmaResumen = '';
  firmaRecientes = '';
  ultimaConsulta = 0;
 }
 await actualizarResumen();
}

export async function actualizarResumen() {
 if (actualizando || document.hidden || !ctx.isCurrent('resumen')) return;
 if (Date.now() - ultimaConsulta < 4000 && firmaResumen) return;
 actualizando = true;
 try {
  const datos = await ctx.api('resumen_restaurantes', {});
  if (!ctx.isCurrent('resumen') || !$('sales-chart')) return;
  ultimaConsulta = Date.now();
  const firma = JSON.stringify([datos.restaurantes,datos.abiertos,datos.activos,datos.ventas_hoy,datos.productos,datos.serie,datos.populares]);
  if (firma !== firmaResumen) {
   for (const key of ['restaurantes','activos','ventas_hoy','productos']) {
    const nodo = document.querySelector(`[data-metric="${key}"]`);
    const valor = key === 'ventas_hoy' ? money(datos[key]) : String(datos[key]);
    if (nodo.textContent !== valor) nodo.textContent = valor;
   }
   document.querySelector('[data-metric-note="abiertos"]').textContent = datos.abiertos + ' abiertas ahora';
   dibujarGrafico(datos.serie);
   populares(datos.populares);
   firmaResumen = firma;
  }
  const recientes = JSON.stringify(datos.recientes);
  if (recientes !== firmaRecientes) {
   actualizarFilas(datos.recientes);
   firmaRecientes = recientes;
  }
 } finally { actualizando = false; }
}

function dibujarGrafico(serie) {
 const root = $('sales-chart');
 if (!root.children.length) {
  for (let i = 0; i < 7; i++) {
   const dia = document.createElement('div');
   dia.className = 'chart-day';
   const bar = document.createElement('button');
   bar.className = 'chart-bar';
   bar.type = 'button';
   const label = document.createElement('span');
   dia.append(bar,label);
   root.append(dia);
  }
 }
 const maximo = Math.max(...serie.map(x => x.ventas), 1);
 for (let i = 0; i < serie.length; i++) {
  const dato = serie[i];
  const nodo = root.children[i];
  const bar = nodo.querySelector('button');
  const label = new Date(dato.dia+'T12:00:00').toLocaleDateString('es-CO',{weekday:'short'}).replace('.','');
  nodo.querySelector('span').textContent = label;
  bar.style.height = Math.max(5, dato.ventas/maximo*155) + 'px';
  bar.classList.toggle('is-today', i === serie.length-1);
  bar.title = `${label}: ${money(dato.ventas)} · ${dato.pedidos} pedidos simulados`;
  bar.setAttribute('aria-label',bar.title);
  bar.onclick = () => ctx.notify(bar.title);
 }
 $('week-total').textContent = money(serie.reduce((a,x) => a+x.ventas,0));
}

function populares(rows) {
 const root = $('top-restaurants');
 for (const dato of rows) {
  let item = root.querySelector(`[data-restaurant="${dato.id}"]`);
  if (!item) {
   item = document.createElement('button');
   item.type = 'button';
   item.className = 'top-restaurant';
   item.dataset.restaurant = dato.id;
   item.append(foto(dato.foto,dato.nombre));
   const texto = document.createElement('span');
   texto.innerHTML = '<b></b><small></small>';
   item.append(texto);
   const contador = document.createElement('strong');
   item.append(contador);
   item.onclick = () => abrirRestaurante(dato.id).catch(mensajeError);
   root.append(item);
  }
  item.querySelector('b').textContent = dato.nombre;
  item.querySelector('small').textContent = dato.categoria;
  item.querySelector('strong').textContent = dato.pedidos;
 }
}

function actualizarFilas(rows, target='platform-orders') {
 const root = $(target);
 const validos = new Set(rows.map(x => x.id));
 for (const row of [...root.children]) if (!validos.has(row.dataset.order)) row.remove();
 for (const [index,dato] of rows.entries()) {
  let row = root.querySelector(`[data-order="${dato.id}"]`);
  if (!row) {
   row = document.createElement('tr');
   row.dataset.order = dato.id;
   row.innerHTML = '<td class="order-code"></td><td><div class="order-restaurant"><img alt=""><span></span></div></td><td class="order-client"></td><td class="order-status"></td><td class="order-total"></td><td class="order-time"></td><td></td>';
   const b = boton('Ver', () => abrirRestaurante(dato.restaurante).catch(mensajeError),'table-action');
   row.lastElementChild.append(b);
   root.append(row);
  }
  const referencia=root.children[index];if(referencia!==row)root.insertBefore(row,referencia||null);
  row.querySelector('.order-code').textContent = '#'+dato.id.slice(0,6).toUpperCase();
  row.querySelector('.order-restaurant img').src = dato.restaurante_foto;
  row.querySelector('.order-restaurant img').alt = '';
  row.querySelector('.order-restaurant span').textContent = dato.restaurante_nombre;
  row.querySelector('.order-client').textContent = dato.cliente;
  const estado = row.querySelector('.order-status');
  if (estado.dataset.status !== dato.estado) { estado.innerHTML = etiqueta(dato.estado);estado.dataset.status=dato.estado; }
  row.querySelector('.order-total').textContent = money(dato.total);
  row.querySelector('.order-time').textContent = fecha(dato.fecha);
 }
}

export async function pedidos(contenedor){
 const cocinas=await ctx.api('listar_restaurantes',{});
 if(!ctx.isCurrent('pedidos'))return;
 contenedor.innerHTML='<section class="panel glass platform-order-page"><div class="panel-header"><div><span class="eyebrow">DEL ANTOJO A LA PUERTA</span><h2>Pedidos de todas las cocinas</h2><p class="muted">Actividad de la simulación, con seguimiento de cada entrega.</p></div><span class="simulation-pill static">Simulación</span></div><div class="platform-order-filters"><input id="platform-order-search" type="search" placeholder="Pedido, cliente o cocina" aria-label="Buscar pedidos"><select id="platform-order-status" aria-label="Filtrar por estado"><option value="">Todos los estados</option></select><select id="platform-order-restaurant" aria-label="Filtrar por restaurante"><option value="">Todas las cocinas</option></select></div><div class="catalog-counter"><b id="platform-order-count"></b><span>Seguimiento de domicilios</span></div><div class="table-wrap"><table class="platform-orders"><thead><tr><th>Pedido</th><th>Cocina</th><th>Cliente</th><th>Estado</th><th>Total</th><th>Hora</th><th></th></tr></thead><tbody id="platform-order-list"></tbody></table></div></section>';
 for(const [estado,label] of Object.entries(estados)){const o=document.createElement('option');o.value=estado;o.textContent=label;$('platform-order-status').append(o)}
 for(const r of cocinas){const o=document.createElement('option');o.value=r.id;o.textContent=r.nombre;$('platform-order-restaurant').append(o)}
 for(const id of ['platform-order-search','platform-order-status','platform-order-restaurant'])$(id).addEventListener(id.endsWith('search')?'input':'change',()=>filtrarPedidos(true));
 ultimoPedido=0;firmaPedidos='';await actualizarPedidos();
}

function filtrarPedidos(forzar=false){
 if(!$('platform-order-list'))return;
 const q=normalizar($('platform-order-search').value),estado=$('platform-order-status').value,cocina=$('platform-order-restaurant').value;
 const rows=pedidosPlataforma.filter(p=>(!estado||p.estado===estado)&&(!cocina||p.restaurante===cocina)&&normalizar(p.id+' '+p.cliente+' '+p.restaurante_nombre).includes(q));
 const firma=JSON.stringify(rows);
 if(forzar||firma!==firmaPedidos){actualizarFilas(rows,'platform-order-list');$('platform-order-count').textContent=rows.length+' pedidos';firmaPedidos=firma;}
}

export async function actualizarPedidos(){
 if(actualizando||!ctx.isCurrent('pedidos')||!$('platform-order-list')||document.hidden)return;
 if(Date.now()-ultimoPedido<4000&&firmaPedidos)return;
 actualizando=true;
 try{const rows=await ctx.api('listar_pedidos_restaurantes',{});if(!ctx.isCurrent('pedidos'))return;pedidosPlataforma=rows;ultimoPedido=Date.now();filtrarPedidos()}finally{actualizando=false}
}

export async function catalogo(contenedor) {
 restaurantes = await ctx.api('listar_restaurantes', {});
 if (!ctx.isCurrent('restaurantes')) return;
 contenedor.innerHTML = `<section class="catalog-heading"><div><span class="eyebrow">30 COCINAS. MIL ANTOJOS.</span><h2>¿Qué se cocina hoy?</h2><p>De la masa al carbón, del maíz al rollo. Hay un parche para cada antojo.</p></div><span class="simulation-pill static">Catálogo simulado</span></section><section class="catalog-controls glass"><div class="catalog-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6"></circle><path d="m15 15 5 5"></path></svg><input id="restaurant-search" type="search" placeholder="Restaurante, especialidad o barrio" aria-label="Buscar restaurantes"></div><div class="catalog-switches"><label class="switch-label"><input id="only-open" type="checkbox"><span>Solo abiertas</span></label><button id="only-favorites" class="chip">Mis favoritos</button></div></section><div class="cuisine-filters" id="cuisine-filters"></div><div class="catalog-counter"><b id="restaurant-count"></b><span>Cali · Solo domicilios</span></div><div class="restaurant-grid" id="restaurant-grid"></div><p class="simulation-note">Negocios y menús ficticios para probar la plataforma. Fotografías de referencia.</p>`;
 $('restaurant-search').value = busqueda;
 $('only-open').checked = soloAbiertos;
 $('only-favorites').classList.toggle('selected',favoritosFiltro);
 const categorias = ['',...new Set(restaurantes.map(r => r.categoria))];
 for (const tipo of categorias) {
  const b = boton(tipo || 'Todo el parche', () => {
   categoria = tipo;
   for (const child of $('cuisine-filters').children) child.classList.toggle('selected',child === b);
   pintarRestaurantes();
  },'cuisine-chip'+(categoria === tipo?' selected':''));
  $('cuisine-filters').append(b);
 }
 $('restaurant-search').oninput = e => { busqueda=e.target.value;pintarRestaurantes(); };
 $('only-open').onchange = e => { soloAbiertos=e.target.checked;pintarRestaurantes(); };
 $('only-favorites').onclick = e => { favoritosFiltro=!favoritosFiltro;e.currentTarget.classList.toggle('selected',favoritosFiltro);pintarRestaurantes(); };
 pintarRestaurantes();
}

function pintarRestaurantes() {
 const root = $('restaurant-grid');
 if (!root) return;
 const q = normalizar(busqueda);
 const rows = restaurantes.filter(r => (!categoria || r.categoria===categoria) && (!soloAbiertos || r.estado==='abierto') && (!favoritosFiltro || favoritos.has(r.id)) && normalizar(r.nombre+' '+r.categoria+' '+r.barrio).includes(q));
 $('restaurant-count').textContent = rows.length + (rows.length===1?' restaurante':' restaurantes');
 const ids = new Set(rows.map(r => r.id));
 for (const item of [...root.children]) if (!ids.has(item.dataset.restaurant)) item.remove();
 for (const r of rows) {
  let card = root.querySelector(`[data-restaurant="${r.id}"]`);
  if (!card) {
   card = document.createElement('article');
   card.className = 'restaurant-card glass tone-'+r.color;
   card.dataset.restaurant = r.id;
   const media = document.createElement('div');
   media.className = 'restaurant-cover';
   const abrir = boton('',()=>abrirRestaurante(r.id).catch(mensajeError),'cover-button');
   abrir.setAttribute('aria-label','Ver menú de '+r.nombre);
   abrir.append(foto(r.foto,r.categoria+' de '+r.nombre));
   media.append(abrir);
   const badge = document.createElement('span');
   badge.className = 'cuisine-label';badge.textContent=r.categoria;media.append(badge);
   const heart = boton('',()=>{if(favoritos.has(r.id))favoritos.delete(r.id);else favoritos.add(r.id);localStorage.setItem('parche.favoritos',JSON.stringify([...favoritos]));pintarRestaurantes()},'favorite-button');
   heart.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"></path></svg>';
   heart.setAttribute('aria-label','Favorito: '+r.nombre);media.append(heart);
   card.append(media);
   const body = document.createElement('div');body.className='restaurant-body';
   body.innerHTML=`<div class="row"><span class="restaurant-area">${esc(r.barrio)}</span><span class="restaurant-rating">★ ${esc(r.valoracion.toFixed(1))}</span></div><h3>${esc(r.nombre)}</h3><p>${esc(r.descripcion)}</p><div class="restaurant-facts"><span>${r.tiempo_min}–${r.tiempo_max} min</span><i></i><span>Envío ${money(r.envio)}</span></div><div class="restaurant-footer"><div class="restaurant-status"></div></div>`;
   body.querySelector('.restaurant-footer').append(boton('Ver menú  ↗︎',()=>abrirRestaurante(r.id).catch(mensajeError),'menu-link'));
   card.append(body);
   root.append(card);
  }
  const heart=card.querySelector('.favorite-button');heart.classList.toggle('is-favorite',favoritos.has(r.id));heart.setAttribute('aria-pressed',String(favoritos.has(r.id)));
  card.querySelector('.restaurant-status').innerHTML=etiqueta(r.estado);
 }
 if (!rows.length) {
  root.innerHTML='<div class="empty catalog-empty"><b>Ese antojo aún no aparece.</b><p>Prueba con otro nombre, cambia la especialidad o quita un filtro.</p></div>';
 }
}

export async function abrirRestaurante(id) {
 const datos = await ctx.api('detalle_restaurante',{restaurante:id});
 const r = datos.restaurante;
 const carrito = new Map();
 const dom = document.createElement('div');dom.className='restaurant-detail';
 dom.innerHTML=`<div class="restaurant-sheet-hero"><img src="${esc(r.foto)}" alt="${esc(r.categoria)}"><div class="sheet-hero-copy"><span class="eyebrow">${esc(r.categoria.toUpperCase())} / ${esc(r.barrio.toUpperCase())}</span><h3>${esc(r.nombre)}</h3><span>${r.tiempo_min}–${r.tiempo_max} min · Envío ${money(r.envio)}</span></div><span class="sheet-state">${etiqueta(r.estado)}</span></div><div class="sheet-description"><p>${esc(r.descripcion)}</p><span class="reference-label">Fotografía de referencia · Cocina ficticia</span></div><div class="restaurant-sheet-layout"><section><div class="sheet-section-heading"><h3>Hecho para el antojo</h3><span>${datos.menu.length} platos</span></div><div class="sheet-products"></div></section><aside class="sheet-order glass"><span class="eyebrow">PEDIDO DE PRUEBA</span><h3>Arma tu parche.</h3><form id="simulation-form"><label>Cliente<input name="cliente" maxlength="100" required></label><label>Barrio de entrega<input name="barrio" maxlength="100" required></label><div class="simulation-basket"></div><label>Nota para cocina<textarea name="observacion" maxlength="100" placeholder="¿Alguna preferencia?"></textarea></label><div class="simulation-totals"><div><span>Productos</span><b class="simulation-subtotal">${money(0)}</b></div><div><span>Envío</span><b>${money(r.envio)}</b></div><div class="grand-total"><span>Total</span><strong class="simulation-total">${money(0)}</strong></div></div><p class="form-error" role="alert"></p><button class="primary wide" type="submit">Crear pedido simulado ↗︎</button><small>Este pedido no afecta la caja ni el inventario reales.</small></form></aside></div><section class="sheet-recent"><div class="sheet-section-heading"><h3>Últimos pedidos de esta cocina</h3><span>Simulación</span></div><div class="sheet-order-list"></div></section><div class="sheet-admin"></div>`;
 const form=dom.querySelector('form');form.elements.cliente.value=nombres[Number(id.slice(-2))%nombres.length];form.elements.barrio.value=r.barrio;
 function actualizarCarrito() {
  const list=dom.querySelector('.simulation-basket');list.replaceChildren();let subtotal=0;
  for (const [pid,n] of carrito) {
   const p=datos.menu.find(x=>x.id===pid);subtotal+=p.precio*n;
   const linea=document.createElement('div');linea.className='simulation-line';linea.innerHTML=`<div><b>${esc(p.nombre)}</b><small>${money(p.precio*n)}</small></div>`;
   const qty=document.createElement('div');qty.className='quantity-control';
   qty.append(boton('−',()=>{if(n===1)carrito.delete(pid);else carrito.set(pid,n-1);actualizarCarrito()},'icon-button'),document.createTextNode(n),boton('+',()=>{if(n<Math.min(p.stock,20))carrito.set(pid,n+1);actualizarCarrito()},'icon-button'));
   linea.append(qty);list.append(linea);
  }
  if(!carrito.size)list.innerHTML='<div class="basket-hint">Elige algo rico del menú para empezar.</div>';
  dom.querySelector('.simulation-subtotal').textContent=money(subtotal);dom.querySelector('.simulation-total').textContent=money(carrito.size?subtotal+r.envio:0);
  form.querySelector('button[type=submit]').disabled=!carrito.size || r.estado!=='abierto';
 }
 for (const p of datos.menu) {
  const card=document.createElement('article');card.className='sheet-product';
  card.append(foto(p.foto,p.nombre));
  const text=document.createElement('div');text.className='sheet-product-copy';text.innerHTML=`${p.destacado?'<span class="popular-label">Favorito de la cocina</span>':''}<h4>${esc(p.nombre)}</h4><p>${esc(p.descripcion)}</p><div class="row"><b>${money(p.precio)}</b><small>${p.stock>0?'Disponible':'Agotado'}</small></div>`;
  card.append(text);
  const add=boton('+',()=>{const n=carrito.get(p.id)||0;if(n>=Math.min(p.stock,20))return;carrito.set(p.id,n+1);actualizarCarrito()},'product-plus');add.disabled=p.stock===0 || r.estado!=='abierto';add.setAttribute('aria-label','Agregar '+p.nombre);card.append(add);dom.querySelector('.sheet-products').append(card);
 }
 actualizarCarrito();
 let identificador=crypto.randomUUID(),ultimo='';
 form.onsubmit=async e=>{
  e.preventDefault();const b=form.querySelector('button[type=submit]');b.disabled=true;
  try {
   const payload={restaurante:id,cliente:form.elements.cliente.value.trim(),barrio:form.elements.barrio.value.trim(),observacion:form.elements.observacion.value,lineas:[...carrito].map(([producto,cantidad])=>({producto,cantidad}))};
   if(JSON.stringify(payload)!==ultimo){identificador=crypto.randomUUID();ultimo=JSON.stringify(payload)}
   const result=await ctx.api('simular_pedido_restaurante',payload,identificador);
   ultimaConsulta=0;firmaResumen='';ctx.notify('Pedido #'+result.id.slice(0,6).toUpperCase()+' creado · '+money(result.total));
   await abrirRestaurante(id);
  } catch(e){form.querySelector('.form-error').textContent=e.message;b.disabled=false;}
 };
 const list=dom.querySelector('.sheet-order-list');
 for (const p of datos.pedidos.slice(0,8)) {
  const row=document.createElement('div');row.className='sheet-order-row';row.innerHTML=`<div><b>#${esc(p.id.slice(0,6).toUpperCase())} · ${esc(p.cliente)}</b><small>${esc(p.barrio)} · ${fecha(p.fecha)}</small></div>${etiqueta(p.estado)}<strong>${money(p.total)}</strong>`;
  if(siguiente[p.estado])row.append(boton(p.estado==='listo'?'Despachar':p.estado==='en ruta'?'Confirmar entrega':'Avanzar',async()=>{
   try {
    if(p.estado==='listo')return elegirDomiciliario(p,id);
    await ctx.api('estado_pedido_simulado',{pedido:p.id,estado:siguiente[p.estado]});ultimaConsulta=0;firmaResumen='';await abrirRestaurante(id);ctx.notify('Estado actualizado');
   }catch(e){mensajeError(e)}
  },'secondary'));
  list.append(row);
 }
 const admin=dom.querySelector('.sheet-admin');admin.append(boton(r.estado==='abierto'?'Pausar esta cocina':'Reabrir esta cocina',async()=>{
  try {await ctx.api('estado_restaurante_simulado',{restaurante:id,estado:r.estado==='abierto'?'pausado':'abierto'});restaurantes=restaurantes.map(x=>x.id===id?{...x,estado:r.estado==='abierto'?'pausado':'abierto'}:x);pintarRestaurantes();ultimaConsulta=0;firmaResumen='';await abrirRestaurante(id)}catch(e){mensajeError(e)}
 },'secondary'));
 ctx.modal('El menú de '+r.nombre,body=>body.append(dom));$('modal').classList.add('restaurant-modal');
}

function elegirDomiciliario(p,id) {
 ctx.modal('Despachar pedido',body=>{
  const label=document.createElement('label');label.textContent='Domiciliario asignado';const select=document.createElement('select');
  for(const name of ['Carlos Rivas','Ezequiel López','Daniel Torres']){const option=document.createElement('option');option.value=name;option.textContent=name;select.append(option)}
  label.append(select);body.append(label,boton('Confirmar despacho',async()=>{try{await ctx.api('estado_pedido_simulado',{pedido:p.id,estado:'en ruta',domiciliario:select.value});ultimaConsulta=0;firmaResumen='';await abrirRestaurante(id);ctx.notify('Pedido en ruta')}catch(e){mensajeError(e)}}));
 });
}
