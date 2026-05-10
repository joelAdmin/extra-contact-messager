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

1.  Ve a la configuración de tu página de Facebook.
2.  Busca la sección de "Mensajería" o "Integraciones de Mensajería".
3.  Configura tu webhook apuntando a la URL pública de tu aplicación (ej: `https://tu-dominio.com/webhook`) y usa el `VERIFY_TOKEN` que definiste. Asegúrate de suscribirte a los eventos de mensajes.

### Ejecución del Bot

```bash
python app.py
```

El bot se iniciará en el puerto 5000 (por defecto). Asegúrate de que este puerto sea accesible públicamente si estás desplegándolo en un servidor.

### Dependencias

*   Flask
*   Requests
*   Pandas
*   Openpyxl
*   python-dotenv
*   Loguru (aunque actualmente usa `print` para la mayoría de logs)

### Formatos de Número Soportados

La función `extraer_numero_telefono` intenta identificar números en formatos como:
*   `+57 310 552 3667`
*   `(310) 552-3667`
*   `310-552-3667`
*   `310 552 3667`
*   `3105523667` (10 dígitos)
*   `573105523667` (con código de país)
