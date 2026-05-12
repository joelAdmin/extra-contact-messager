# Bot de Messenger para Captura de Leads

Este proyecto implementa un bot de Facebook Messenger utilizando Flask para capturar información de contacto (principalmente números de teléfono) de los usuarios y notificar al administrador a través de WhatsApp y/o Telegram.

## Análisis del Proyecto

El bot funciona como un webhook que escucha los mensajes entrantes de una página de Facebook. Al recibir un mensaje, intenta extraer un número de teléfono.

-   **Si se detecta un número de teléfono:**
    -   Lo guarda en `contactos.txt` y `contactos.xlsx`.
    -   Responde al usuario confirmando la recepción del número.
    -   Marca al usuario como respondido para evitar consultas futuras.
    -   Envía una alerta al administrador a través de WhatsApp y/o Telegram.
-   **Si no se detecta un número de teléfono:**
    -   Si es la primera interacción con el usuario, solicita que comparta su número de teléfono.
    -   Marca al usuario como respondido para evitar solicitar el número nuevamente.

La persistencia de los usuarios respondidos se maneja a través del archivo `usuarios_respondidos.json`.

## Documentación de Uso y Configuración

### Prerrequisitos

*   Python 3.x
*   Un entorno virtual (recomendado)
*   Acceso a una página de Facebook y una cuenta de WhatsApp Business (API Cloud) o un bot de Telegram.
*   Cuenta de Telegram (gratuita)

### Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd bot_app
    ```
2.  **Crear y activar un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```
3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuración

Crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables, reemplazando los valores de ejemplo con tu información real:

```dotenv
# Tokens de Facebook
FACEBOOK_PAGE_ACCESS_TOKEN=TU_TOKEN_DE_ACCESO_AQUI
VERIFY_TOKEN=TU_PALABRA_SECRETA_PARA_VERIFICAR_WEBHOOK
PHONE_NUMBER_ID=EL_ID_DE_TU_NUMERO_DE_WHATSAPP_BUSINESS

# Configuración de Destino (Elige UNA o ambas)
# Opcion 1: WhatsApp Business para alertas
MI_NUMERO_WHATSAPP=TU_NUMERO_DE_WHATSAPP_PARA_ALERTAS # Ej: 521234567890

# Opcion 2: Telegram para alertas
TELEGRAM_BOT_TOKEN=EL_TOKEN_DE_TU_BOT_DE_TELEGRAM
MI_ID_TELEGRAM=TU_ID_DE_CHAT_DE_TELEGRAM

# Archivo para rastrear usuarios que ya recibieron respuesta
ARCHIVO_RESPONDIDOS=usuarios_respondidos.json
```

### Configuración del Webhook en Facebook

1.  Ve al Facebook Developers Portal.
2.  Selecciona tu aplicación y ve a "Productos" → "Messenger" → "Configuración"
3.  En la sección "Webhook", haz clic en "Configurar Webhook"
4.  Configura tu webhook apuntando a la URL pública de tu aplicación (ej: `https://tu-dominio.com/webhook`) y usa el `VERIFY_TOKEN` que definiste. Asegúrate de suscribirte a los eventos de mensajes.
5. Suscríbete a los eventos: messages, messaging_postbacks, message_deliveries, message_reads Haz clic en "Verificar y guardar"
6. En la sección "Página", selecciona tu página y suscríbela a los eventos.

# Configuración del Bot de Telegram (Paso a Paso)

Para recibir las alertas de los leads en Telegram, necesitas crear un bot y obtener tu ID de chat personal. Sigue estos pasos:

### Paso 1: Crear el Bot con @BotFather

1. **Abre Telegram** en tu teléfono o computadora.
2. **Busca el usuario @BotFather** (es el bot oficial de Telegram para crear bots).
   - En la barra de búsqueda, escribe: `@BotFather`
   - Haz clic en el resultado para abrir la conversación.
3. **Inicia la conversación** con `@BotFather` enviando el comando:
```bash
/start
```
4. **Crea un nuevo bot** con `@BotFather` enviando el comando:
```text
/newbot
```
5. Responde a las preguntas de **@BotFather**:
    - **Nombre del bot:** Elige un nombre visible para tu bot. Ej: Mi Bot Notificador
    - **Username del bot:** Elige un nombre de usuario único que termine en _bot. Ej: mi_bot_notificador_bot

6. Guarda el Token
    - **@BotFather** te responderá con un mensaje como este:
        ```text
        Done! Congratulations on your new bot. You will find it at t.me/mi_bot_notificador_bot
        Use this token to access the HTTP API:1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
        ```
    - Copia el token completo (incluyendo el número y los dos puntos). Este es tu `TELEGRAM_BOT_TOKEN`.

### Paso 2: Obtener tu Chat ID Personal
El `chat_id` es el identificador único de tu conversación con el bot. El bot necesita saber a quién enviarle las alertas.
### Método Rápido (Recomendado):
1. Háblale a tu bot recién creado:
    - Busca tu bot en Telegram usando su username. Ej: @mi_bot_notificador_bot
    - Envía cualquier mensaje. Por ejemplo: /start o "Hola"
2. Obtén tu `chat_id usando este comando en tu servidor o terminal local (reemplaza TU_TOKEN con el token que copiaste):
```text
curl -s "https://api.telegram.org/botTU_TOKEN/getUpdates" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['message']['chat']['id'])"
```
O si prefieres ver toda la respuesta:
```text 
curl -s "https://api.telegram.org/botTU_TOKEN/getUpdates" | python3 -m json.tool
```
3. Busca el número en la respuesta. Deberías ver algo como:
```text
 {
    "ok": true,
    "result": [
        {
            "message": {
                chat": {
                    "id": 1318649767,  ← ESTE es tu MI_ID_TELEGRAM
                    "first_name": "Tu Nombre",
                    "type": "private"
                }
            }
        }
    ]
}        
```   

### Método Alternativo (con @userinfobot):
1. En Telegram, busca el bot **@userinfobot**
2. Envía `/start`
3. El bot te responderá con tu información, incluyendo tu `Id de usuario.

⚠️ **Importante:** El bot **no puede** enviarte el primer mensaje. Debes escribirle al menos una vez para que Telegram registre tu `chat_id`.

### Paso 3: Verificar que el Bot Funciona

Antes de configurar el archivo `.env`, prueba que el bot puede enviarte mensajes: 
```text
# Reemplaza TU_TOKEN con el token de tu bot
# Reemplaza TU_CHAT_ID con el número que obtuviste
curl -s "https://api.telegram.org/botTU_TOKEN/sendMessage?chat_id=TU_CHAT_ID&text=Prueba%20de%20conexión"
```

**Si ves:** ``{"ok":true,...}`` → ✅ El bot funciona correctamente y recibirás el mensaje en Telegram.

**Si ves:** ``{"ok":false,"error_code":400,"description":"Bad Request: chat not found"}`` → ❌ El `chat_id` es incorrecto o no has iniciado la conversación con el bot.

### Paso 4:  Agregar las Credenciales al archivo `.env`
Una vez que tengas el token y el chat_id, actualiza tu archivo `.env`:
```text    
# Credenciales de Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
MI_ID_TELEGRAM=1318649768
``` 

### Paso 5: Reiniciar el Bot
Después de actualizar el .env, reinicia el servicio:
```text
sudo systemctl restart bot-facebook.service
```
### Ejecución del Bot

```bash
python app.py
```

El bot se iniciará en el puerto 5000 (por defecto). Asegúrate de que este puerto sea accesible públicamente si estás desplegándolo en un servidor.

### Producción con Gunicorn y Systemd
1. Crear el archivo de servicio:
```bash
sudo nano /etc/systemd/system/bot-facebook.service
```
2. Contenido del archivo de servicio:
```bash
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
3. Iniciar el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl start bot-facebook.service
sudo systemctl enable bot-facebook.service  # Para iniciar automáticamente al reiniciar
```

### Comandos útiles para Systemd
```bash
# Estado del servicio
sudo systemctl status bot-facebook.service

# Reiniciar el servicio
sudo systemctl restart bot-facebook.service

# Detener el servicio
sudo systemctl stop bot-facebook.service

# Verificar si está habilitado
sudo systemctl is-enabled bot-facebook.service
```

### Ver Logs en Producción
```bash
# Ver logs en tiempo real
sudo journalctl -u bot-facebook.service -f

# Ver las últimas 100 líneas
sudo journalctl -u bot-facebook.service -n 100

# Ver logs desde hace 1 hora
sudo journalctl -u bot-facebook.service --since "1 hour ago"

# Ver logs con grep
sudo journalctl -u bot-facebook.service | grep "Número extraído"
```

### Dependencias

*   Flask
*   Requests
*   Pandas
*   Openpyxl
*   python-dotenv
*   Loguru (aunque actualmente usa `print` para la mayoría de logs)

### Formatos de Número Soportados

La función `extraer_numero_telefono` intenta identificar números en formatos como:
*   `+57 310 553 3667`
*   `(310) 553-3667`
*   `310-553-3667`
*   `310 553 3667`
*   `3105533667` (10 dígitos)
*   `573105533667` (con código de país)

### Licencia

Este proyecto es de uso libre. Puedes modificarlo y adaptarlo según tus necesidades.


