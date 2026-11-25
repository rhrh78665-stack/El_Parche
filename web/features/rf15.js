export default {
  "n": 15,
  "key": "cobrar_pedido",
  "title": "Cobrar pedido",
  "group": "caja",
  "fields": [
    {
      "key": "pedido",
      "label": "Pedido",
      "type": "pedido"
    },
    {
      "key": "pagos",
      "label": "Distribución del pago",
      "type": "repeat",
      "columns": [
        {
          "key": "medio",
          "label": "Medio",
          "type": "select",
          "options": [
            "efectivo",
            "datáfono",
            "Nequi",
            "Daviplata",
            "transferencia",
            "plataforma"
          ]
        },
        {
          "key": "valor",
          "label": "Valor",
          "type": "money"
        },
        {
          "key": "referencia",
          "label": "Referencia bancaria",
          "type": "text",
          "required": false
        }
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
