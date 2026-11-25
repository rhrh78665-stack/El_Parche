export default {
  "n": 30,
  "key": "guardar_usuario",
  "title": "Crear o editar integrante",
  "group": "equipo",
  "fields": [
    {
      "key": "id",
      "label": "Usuario",
      "type": "text"
    },
    {
      "key": "nombre",
      "label": "Nombre completo",
      "type": "text"
    },
    {
      "key": "rol",
      "label": "Rol",
      "type": "select",
      "options": [
        "administrador",
        "cajera",
        "mesero",
        "cocina",
        "domiciliario"
      ]
    },
    {
      "key": "pin",
      "label": "PIN de 8 a 64 dígitos",
      "type": "password",
      "required": false
    },
    {
      "key": "activo",
      "label": "Acceso habilitado",
      "type": "bool"
    }
  ],
  "kind": "form",
  "description": ""
};
