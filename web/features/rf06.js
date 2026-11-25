export default {
  "n": 6,
  "key": "cancelar_pedido",
  "title": "Cancelar pedido",
  "group": "pedidos",
  "fields": [
    {
      "key": "pedido",
      "label": "Pedido",
      "type": "pedido"
    },
    {
      "key": "motivo",
      "label": "Motivo",
      "type": "select",
      "options": [
        "cliente desistió",
        "demora",
        "falta de insumo",
        "error de registro"
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
