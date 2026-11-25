const permitidas = new Set(['registrar_pedido', 'pedido_mesa', 'cobrar_pedido']);
const lecturas = new Set(['cola_pedidos','pedidos_demorados','comandas','buscar_cliente','cuadre_domiciliario','consultar_existencias','alertas_stock','menu_disponible','reporte_ventas','historial_cajas','reporte_atencion','mis_domicilios','ver_auditoria','listar_usuarios','pedidos_operables','detalle_pedido','lineas_operables','modificadores_producto','estado_caja','integridad_auditoria','preferencias_operacion']);
let propietario = sessionStorage.getItem('parche.usuario') || '';
let sincronizando = false;
const disponible = new Promise((resolve, reject) => {
 const solicitud = indexedDB.open('parche-operacion-v2', 1);
 solicitud.onupgradeneeded = () => {
  solicitud.result.createObjectStore('cola', {keyPath: 'id'});
  solicitud.result.createObjectStore('cache', {keyPath: 'id'});
 };
 solicitud.onsuccess = () => resolve(solicitud.result);
 solicitud.onerror = () => reject(new Error('No se pudo abrir el almacenamiento del dispositivo.'));
});
async function guardar(almacen, valor) {
 const db = await disponible;
 return new Promise((resolve, reject) => {
  const t = db.transaction(almacen, 'readwrite');
  t.objectStore(almacen).put(valor);
  t.oncomplete = resolve;
  t.onerror = () => reject(new Error('No hay espacio para conservar la operación.'));
 });
}
async function borrar(almacen, id) {
 const db = await disponible;
 return new Promise((resolve, reject) => {
  const t = db.transaction(almacen, 'readwrite');
  t.objectStore(almacen).delete(id);
  t.oncomplete = resolve;
  t.onerror = reject;
 });
}
async function registros(almacen) {
 const db = await disponible;
 return new Promise((resolve, reject) => {
  const q = db.transaction(almacen).objectStore(almacen).getAll();
  q.onsuccess = () => resolve(q.result);
  q.onerror = reject;
 });
}
export async function pendientes() {
 return (await registros('cola')).filter(x => x.usuario === propietario).sort((a,b) => a.fecha - b.fecha);
}
export async function descartar(id) {
 const item = (await pendientes()).find(x => x.id === id);
 if (!item) throw new Error('Operación no encontrada.');
 if (item.estado !== 'rechazada') throw new Error('Solo se descartan operaciones rechazadas por el servidor. Verifica primero su estado.');
 await borrar('cola', id);
}
async function red(path, data, id) {
 const r = await fetch(path, {method: data ? 'POST' : 'GET', headers: {'Content-Type':'application/json','X-Parche':'1',...(id ? {'Idempotency-Key':id} : {})},body: data ? JSON.stringify(data) : undefined});
 const result = await r.json();
 if (!r.ok) {
  const error = new Error(result.error || 'No se pudo completar la operación.');
  error.http = r.status;
  throw error;
 }
 return result;
}
export async function sincronizar() {
 if (sincronizando) return;
 sincronizando = true;
 try {
  for (const item of await pendientes()) {
   if (item.estado === 'rechazada') break;
   try {
    await red(item.path, item.datos, item.id);
    await borrar('cola', item.id);
   } catch (e) {
    if (e.http) {
     item.estado = 'rechazada';
     item.error = e.message;
     await guardar('cola', item);
    }
    break;
   }
  }
 } finally {
  sincronizando = false;
  window.dispatchEvent(new Event('parche-pendientes'));
 }
}
export async function transporte(path, data, id) {
 const clave = path.split('/').pop();
 if (path === '/api/logout' && (await pendientes()).length) throw new Error('Sincroniza o resuelve los pendientes antes de cerrar sesión.');
 const escritura = path.startsWith('/api/accion/') && permitidas.has(clave);
 let item;
 if (escritura) {
  if (!propietario) throw new Error('Inicia sesión antes de registrar operaciones.');
  if (clave !== 'cobrar_pedido') data.id = data.id || id;
  item = {id,path,datos:structuredClone(data),usuario:propietario,fecha:Date.now(),estado:'pendiente'};
  const existente = (await pendientes()).find(x => x.id === id);
  if (existente && JSON.stringify(existente.datos) !== JSON.stringify(item.datos)) throw new Error('El identificador ya corresponde a otra operación.');
  if (existente) item = existente;
  await guardar('cola', item);
 }
 const cacheId = propietario + ':' + path + ':' + JSON.stringify(data || {});
 try {
  const result = await red(path, data, id);
  if (escritura) await borrar('cola', id);
  if (path === '/api/catalogo') {
   propietario = result.usuario.id;
   sessionStorage.setItem('parche.usuario', propietario);
   await guardar('cache', {id:propietario+':catalogo',valor:result,fecha:Date.now()});
  } else if (lecturas.has(clave)) {
   await guardar('cache', {id:cacheId,valor:result,fecha:Date.now()});
  }
  if (path === '/api/logout') {
   for (const v of await registros('cache')) if (v.id.startsWith(propietario+':')) await borrar('cache', v.id);
   sessionStorage.removeItem('parche.usuario');
   propietario = '';
  }
  window.dispatchEvent(new Event('parche-pendientes'));
  return result;
 } catch (e) {
  if (e.http) {
   if (escritura) {
    item.estado='rechazada';item.error=e.message;await guardar('cola',item);
   }
   throw e;
  }
  if (escritura) {
   window.dispatchEvent(new Event('parche-pendientes'));
   return {id:data.id || id,pendiente:true};
  }
  const cached = (await registros('cache')).find(x => x.id === (path === '/api/catalogo' ? propietario+':catalogo' : cacheId));
  if (cached && Date.now()-cached.fecha <= 12*3600*1000) {
   window.dispatchEvent(new Event('parche-offline'));
   const valor=structuredClone(cached.valor);
   if (Array.isArray(valor) && ['cola_pedidos','pedidos_operables'].includes(clave)) {
    for (const q of await pendientes()) {
     if (['registrar_pedido','pedido_mesa'].includes(q.path.split('/').pop()) && !valor.some(x=>x.id===q.datos.id)) valor.push({id:q.datos.id,canal:q.datos.canal||'mesa',mesa:q.datos.mesa||'',estado:'pendiente de sincronizar',fecha:new Date(q.fecha).toISOString(),total:null});
    }
   }
   return valor;
  }
  throw new Error('Sin conexión. Esta pantalla necesita una consulta previa para poder usarse en este dispositivo.');
 }
}
window.addEventListener('online',sincronizar);
setInterval(sincronizar,15000);
