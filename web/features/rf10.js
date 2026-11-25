export default {
  "n": 10,
  "key": "guardar_producto",
  "title": "Crear o editar producto",
  "group": "menu",
  "fields": [
    {
      "key": "id",
      "label": "Código del producto",
      "type": "text"
    },
    {
      "key": "nombre",
      "label": "Nombre",
      "type": "text"
    },
    {
      "key": "categoria",
      "label": "Categoría",
      "type": "text"
    },
    {
      "key": "precio",
      "label": "Precio de venta",
      "type": "money"
    },
    {
      "key": "modificadores",
      "label": "Modificadores permitidos",
      "type": "tags"
    },
    {
      "key": "activo",
      "label": "Disponible en el menú",
      "type": "bool"
    }
  ],
  "kind": "form",
  "description": ""
};
