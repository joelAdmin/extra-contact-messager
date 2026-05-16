# Bot de Messenger para Captura de Leads

Bot multi-tenant con Flask + MongoDB que captura leads desde Facebook Messenger, extrae números telefónicos y notifica al administrador vía Telegram.

## Arquitectura

```
backend/
├── app.py                         # Rutas Flask + orquestación
├── config.py                      # Conexión MongoDB + carga .env
├── setup_client.py                # Script para registrar clientes en BD
├── models/
│   ├── client.py                  # Dataclass Client
│   └── contact.py                 # Dataclass Contact
├── repositories/                  # Patrón Repositorio (ABC + MongoDB)
│   ├── client_repository.py       # CRUD de clientes
│   ├── contact_repository.py      # CRUD de contactos
│   └── user_repository.py         # Estado de usuarios respondidos
├── services/
│   ├── messenger.py               # API Facebook Messenger
│   └── notifications.py           # Alertas Telegram
├── .env                           # Solo MONGODB_URI + DB_TYPE
└── requirements.txt
```

## Flujo del Bot

### Verificación del Webhook (GET /webhook)

```
Facebook envía GET con ?hub.verify_token=<token>
        ↓
ClientRepository.find_by_verify_token(token)
  Busca en colección `clients` de MongoDB
        ↓
  ¿Existe cliente con ese verify_token?
    ├── Sí → responde con challenge (200) ✅
    │         Marca webhook_verified = true en BD
    └── No → 403 Forbidden
```

### Recepción de Mensajes (POST /webhook)

```
Facebook envía POST con payload JSON
        ↓
Extraer page_id del payload: entry[0].id
        ↓
ClientRepository.find_by_page_id(page_id)
  Busca en colección `clients` de MongoDB
        ↓
  ¿Existe cliente con ese page_id?
    ├── No → log + ignora
    └── Sí →
         │
         ├─ Obtener facebook_config → MessengerService
         ├─ Obtener notificaciones  → NotificationService
         ├─ Obtener bot_config      → mensajes personalizados
         │
         └─ Por cada mensaje en el evento:
              │
              ├─ ¿Tiene número telefónico?
              │   ├── Sí → 1. Obtener perfil del usuario (Graph API)
              │   │        2. Guardar Contact en MongoDB
              │   │        3. Marcar usuario como respondido
              │   │        4. Enviar alerta Telegram
              │   │        5. Responder con mensaje_confirmacion
              │   │        6. Actualizar estadísticas del cliente
              │   │
              │   └── No → ¿Ya se le respondió antes?
              │       ├── No → 1. Enviar mensaje_bienvenida
              │       │        2. Marcar como respondido
              │       └── Sí → Ignorar silenciosamente
              │
              └─ Fin del mensaje
```

## Colecciones MongoDB

### `clients` — Clientes (multi-tenant)

| Campo | Tipo | Descripción |
|---|---|---|
| `client_id` | string | Identificador único del cliente |
| `nombre_empresa` | string | Nombre de la empresa |
| `plan` | string | Plan contratado (free, profesional...) |
| `activo` | bool | Si el cliente está activo |
| `facebook_config.page_access_token` | string | Token de página de Facebook |
| `facebook_config.verify_token` | string | Token de verificación del webhook |
| `facebook_config.page_id` | string | ID de la página de Facebook |
| `notificaciones.telegram` | object | Config Telegram (bot_token, chat_id, activo) |
| `bot_config` | object | Mensajes personalizados del bot |
| `estadisticas` | object | Contactos capturados, etc. |

### `contacts` — Leads capturados

| Campo | Tipo | Descripción |
|---|---|---|
| `client_id` | string | Cliente al que pertenece |
| `sender_id` | string | ID del usuario en Messenger |
| `numero_telefono` | string | Número extraído |
| `nombre_usuario` | string | Nombre desde perfil de Facebook |
| `conversacion` | array | Historial de mensajes del chat |
| `estado` | string | nuevo, contactado, etc. |
| `fecha_captura` | datetime | Fecha de captura |

### `user_states` — Control de respondedos

| Campo | Tipo | Descripción |
|---|---|---|
| `client_id` | string | Cliente |
| `sender_id` | string | Usuario |
| `responded_at` | datetime | Cuándo se le respondió |

## Configuración

Crear `.env` en la raíz del proyecto:

```dotenv
DB_TYPE=mongo
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGODB_DB_NAME=plataforma_bots
```

Las credenciales de Facebook y Telegram **no van en .env**. Se almacenan directamente en MongoDB mediante:

```bash
venv/bin/python setup_client.py
```

## Setup de un Cliente

```bash
cd backend
venv/bin/python setup_client.py
```

El script guía interactivamente para ingresar:
- `client_id`, `nombre_empresa`, `plan`
- Credenciales de Facebook (`page_id`, `page_access_token`, `verify_token`)
- Credenciales de Telegram (opcional, `bot_token`, `chat_id`)
- Mensajes personalizados del bot

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

### Desarrollo

```bash
venv/bin/python app.py
```

El servidor se inicia en `http://localhost:5000`.

### Producción con Gunicorn + Systemd

Crear archivo de servicio:

```ini
[Unit]
Description=Bot Facebook Messenger
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/tu-dominio.com/bot_app
Environment="PATH=/var/www/vhosts/tu-dominio.com/bot_app/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/var/www/vhosts/tu-dominio.com/bot_app/venv/bin/gunicorn --bind 127.0.0.1:5001 app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bot-facebook

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start bot-facebook.service
sudo systemctl enable bot-facebook.service
```

### Comandos útiles

```bash
# Estado
sudo systemctl status bot-facebook.service

# Reiniciar
sudo systemctl restart bot-facebook.service

# Logs en tiempo real
sudo journalctl -u bot-facebook.service -f

# Últimas 100 líneas
sudo journalctl -u bot-facebook.service -n 100
```

## Dependencias

- Flask
- Requests
- Pandas + Openpyxl
- python-dotenv
- pymongo[srv]
- dnspython

## DB_TYPE

Variable para seleccionar el motor de base de datos:

| Valor | Estado |
|---|---|
| `mongo` | ✅ Implementado |
| `mysql` | ⏳ Pendiente |
| `postgresql` | ⏳ Pendiente |

## Formatos de Número Soportados

La función `extraer_numero_telefono` identifica números en formatos como:

- `+57 310 553 3667`
- `(310) 553-3667`
- `310-553-3667`
- `310 553 3667`
- `3105533667` (10 dígitos)
- `573105533667` (con código de país)

## Licencia

Este proyecto es de uso libre. Puedes modificarlo y adaptarlo según tus necesidades.
