export default {
  "n": 20,
  "key": "guardar_receta",
  "title": "Definir receta",
  "group": "menu",
  "fields": [
    {
      "key": "producto",
      "label": "Producto",
      "type": "producto"
    },
    {
      "key": "insumos",
      "label": "Ingredientes por unidad vendida",
      "type": "repeat",
      "columns": [
        {
          "key": "insumo",
          "label": "Insumo",
          "type": "insumo"
        },
        {
          "key": "cantidad",
          "label": "Cantidad por producto",
          "type": "number",
          "min": 0.001
        }
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
