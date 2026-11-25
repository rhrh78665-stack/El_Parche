export default {
  "n": 19,
  "key": "guardar_insumo",
  "title": "Crear o editar insumo",
  "group": "inventario",
  "fields": [
    {
      "key": "id",
      "label": "Código",
      "type": "text"
    },
    {
      "key": "nombre",
      "label": "Nombre del insumo",
      "type": "text"
    },
    {
      "key": "unidad",
      "label": "Unidad de medida",
      "type": "select",
      "options": [
        "unidad",
        "gramo",
        "mililitro"
      ]
    },
    {
      "key": "minimo",
      "label": "Existencia mínima",
      "type": "number"
    }
  ],
  "kind": "form",
  "description": ""
};
