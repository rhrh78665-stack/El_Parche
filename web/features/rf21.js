export default {
  "n": 21,
  "key": "registrar_compra",
  "title": "Registrar compra",
  "group": "inventario",
  "fields": [
    {
      "key": "proveedor",
      "label": "Proveedor",
      "type": "text"
    },
    {
      "key": "fecha",
      "label": "Fecha de compra",
      "type": "date"
    },
    {
      "key": "insumos",
      "label": "Insumos recibidos",
      "type": "repeat",
      "columns": [
        {
          "key": "insumo",
          "label": "Insumo",
          "type": "insumo"
        },
        {
          "key": "cantidad",
          "label": "Cantidad",
          "type": "number",
          "min": 0.001
        },
        {
          "key": "costo",
          "label": "Costo total de esta línea",
          "type": "money"
        }
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
