export default {
  "n": 25,
  "key": "ajustar_inventario",
  "title": "Registrar conteo físico",
  "group": "inventario",
  "fields": [
    {
      "key": "insumo",
      "label": "Insumo",
      "type": "insumo"
    },
    {
      "key": "conteo",
      "label": "Cantidad contada",
      "type": "number"
    },
    {
      "key": "motivo",
      "label": "Motivo del ajuste",
      "type": "select",
      "options": [
        "merma",
        "daño",
        "consumo del personal",
        "error"
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
