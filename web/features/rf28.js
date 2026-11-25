export default {
  "n": 28,
  "key": "historial_cajas",
  "title": "Historial de cierres",
  "group": "reportes",
  "fields": [
    {
      "key": "desde",
      "label": "Desde",
      "type": "datetime-local"
    },
    {
      "key": "hasta",
      "label": "Hasta",
      "type": "datetime-local"
    },
    {
      "key": "cajera",
      "label": "Cajera",
      "type": "usuario",
      "required": false
    }
  ],
  "kind": "query",
  "description": ""
};
