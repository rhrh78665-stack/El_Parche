export default {
  "n": 9,
  "key": "registrar_rehecho",
  "title": "Registrar plato rehecho",
  "group": "cocina",
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
        "error de comanda",
        "error de preparación"
      ]
    }
  ],
  "kind": "form",
  "description": ""
};
