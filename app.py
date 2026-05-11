import os
import json
import re
import pandas as pd
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv


# Cargar variables de entorno (para no hardcodear tokens)
load_dotenv()

app = Flask(__name__)

# Diccionario para rastrear usuarios que ya recibieron respuesta
# {sender_id: bool} - True si ya se respondió
usuarios_respondidos = {}

# --- CONFIGURACIÓN ---
FACEBOOK_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
# Configura aquí a dónde quieres recibir la alerta
MI_NUMERO_WHATSAPP = os.getenv('MI_NUMERO_WHATSAPP') # Ej: 521234567890
MI_ID_TELEGRAM = os.getenv('MI_ID_TELEGRAM') # Tu chat ID de Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ARCHIVO_RESPONDIDOS = os.getenv('ARCHIVO_RESPONDIDOS')
# --------------------

# Función para cargar la lista de usuarios respondidos desde un archivo JSON
def cargar_respondidos():
    """Carga la lista de usuarios que ya recibieron respuesta.
    Si el archivo no existe, lo crea vacío."""
    if os.path.exists(ARCHIVO_RESPONDIDOS):
        try:
            with open(ARCHIVO_RESPONDIDOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Si el archivo está corrupto o hay error, crear uno nuevo
            print("[!] Archivo de usuarios corrupto, creando uno nuevo")
            return {}
    else:
        # El archivo no existe, crearlo vacío
        print("[*] Creando archivo usuarios_respondidos.json")
        with open(ARCHIVO_RESPONDIDOS, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}

# Función para guardar la lista de usuarios respondidos en un archivo JSON
def guardar_respondidos(respondidos):
    """Guarda la lista de usuarios que ya recibieron respuesta."""
    try:
        with open(ARCHIVO_RESPONDIDOS, 'w', encoding='utf-8') as f:
            json.dump(respondidos, f, indent=2, ensure_ascii=False)
        print(f"[*] Estado guardado: {len(respondidos)} usuarios respondidos")
        return True
    except Exception as e:
        print(f"[!] Error guardando usuarios_respondidos: {e}")
        return False
    
usuarios_respondidos = cargar_respondidos()
print(f"[*] Cargados {len(usuarios_respondidos)} usuarios que ya respondieron")

# --- 1. FUNCIONES PARA EXTRAER Y GUARDAR ---
def extraer_numero_telefono(texto):
    """
    Busca un número de teléfono en el texto del cliente.
    Soporta múltiples formatos latinoamericanos.
    """
    import re
    
    # Limpiar el texto (remover caracteres extraños)
    texto = texto.strip()
    
    # Patrones de búsqueda (del más específico al más general)
    patrones = [
        # Formato con código de país: +57 310 552 3667
        r'\+\d{1,3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',
        
        # Formato con paréntesis: (310) 552-3667
        r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',
        
        # Formato con guiones: 310-552-3667
        r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',
        
        # Formato con espacios: 310 552 3667
        r'\d{3}[\s]\d{3}[\s]\d{4}',
        
        # Formato continuo (10 dígitos): 3105523667
        r'\d{10,15}',
        
        # Formato con código de país sin más: 573105523667
        r'\d{11,15}',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            numero_raw = match.group()
            # Limpiar el número (solo dígitos)
            numero_limpio = re.sub(r'\D', '', numero_raw)
            
            # Validar que sea un número razonable (entre 7 y 15 dígitos)
            if 7 <= len(numero_limpio) <= 15:
                print(f"[DEBUG] Número encontrado: {numero_raw} -> {numero_limpio}")
                return numero_limpio
    
    print(f"[DEBUG] No se encontró número en: {texto}")
    return None

def guardar_en_excel(numero, nombre_usuario):
    """Guarda el contacto en un archivo Excel con timestamp."""
    archivo_excel = 'contactos.xlsx'
    nueva_fila = {
        'Fecha': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ID_Usuario': nombre_usuario,
        'Numero_Contacto': numero
    }
    
    try:
        # Intentamos leer el archivo existente
        df = pd.read_excel(archivo_excel)
        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    except FileNotFoundError:
        # Si no existe, creamos uno nuevo
        df = pd.DataFrame([nueva_fila])
    
    # Guardamos el archivo
    df.to_excel(archivo_excel, index=False)
    print(f"[+] Contacto guardado: {numero}")

def guardar_en_txt(numero, nombre_usuario):
    """Guarda el contacto en un archivo TXT con timestamp."""
    archivo_txt = 'contactos.txt'
    
    # Crear la línea con los datos
    linea = f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | ID: {nombre_usuario} | Número: {numero}\n"
    
    try:
        # Abrir el archivo en modo append (agregar al final)
        with open(archivo_txt, 'a', encoding='utf-8') as archivo:
            archivo.write(linea)
        print(f"[+] Contacto guardado en TXT: {numero}")
    except Exception as e:
        print(f"[!] Error guardando contacto: {e}")

def enviar_alerta_whatsapp(numero_cliente):
    """Envía una notificación a tu WhatsApp Business."""
    # Usando la API Cloud de WhatsApp Business
    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {FACEBOOK_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": MI_NUMERO_WHATSAPP,
        "type": "text",
        "text": { "body": f"📢 Nuevo lead de Messenger!\nNúmero: {numero_cliente}" }
    }
    try:
        requests.post(url, headers=headers, json=data)
    except Exception as e:
        print(f"Error enviando a WhatsApp: {e}")

def enviar_alerta_telegram(numero_cliente):
    """Envía una notificación a tu Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    print(f"[*] Enviando alerta a Telegram: {numero_cliente}")
    data = {
        "chat_id": MI_ID_TELEGRAM,
        "text": f"📢 *Nuevo lead de Messenger!*\n📞 Número: `{numero_cliente}`",
        "parse_mode": "Markdown"
    }
    print(f"[*] Payload Telegram: {data}")
    try:
        requests.post(url, json=data)
        print(f"[*] Alerta enviada a Telegram para número: {numero_cliente}")
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def responder_a_cliente(recipient_id, mensaje):
    """Envía un mensaje de vuelta al usuario en Messenger."""
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={FACEBOOK_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": mensaje}
    }
    response = requests.post(url, json=data)
    return response.json()

# --- 2. ENDPOINTS DEL SERVIDOR ---
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """Facebook llama a este GET para verificar el webhook."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:
        print("[✓] Webhook verificado correctamente.")
        return challenge, 200
    else:
        return "Error de verificacion", 403

@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    """Recibe los mensajes que los usuarios envian a tu pagina."""
    global usuarios_respondidos
    
    data = request.get_json()
    
    # Verificamos que la data tenga la estructura esperada
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry.get('messaging', []):
                # Ignoramos mensajes enviados por la pagina misma (el bot)
                if messaging_event.get('sender', {}).get('id') == messaging_event.get('recipient', {}).get('id'):
                    continue
                    
                sender_id = messaging_event['sender']['id']
                
                # Si el evento contiene un mensaje de texto
                if messaging_event.get('message') and messaging_event['message'].get('text'):
                    mensaje_texto = messaging_event['message']['text']
                    
                    # --- LOGICA PRINCIPAL MODIFICADA ---
                    
                    # 1. Extraer el numero de telefono del mensaje
                    numero_encontrado = extraer_numero_telefono(mensaje_texto)
                    
                    if numero_encontrado:
                        # SI HAY NÚMERO: Guardar y responder confirmación
                        guardar_en_txt(numero_encontrado, sender_id)
                        
                        # Enviar alerta a WhatsApp y Telegram
                        #enviar_alerta_whatsapp(numero_encontrado)
                        enviar_alerta_telegram(numero_encontrado)
                        
                        # Responder que ya tenemos su número
                        responder_a_cliente(sender_id, f"✅ ¡Gracias! Hemos recibido tu número {numero_encontrado}. En breve nos pondremos en contacto contigo.")
                        print(f"[+] Número extraído y guardado: {numero_encontrado} de usuario {sender_id}")
                        
                        # Marcar como respondido
                        usuarios_respondidos[sender_id] = True
                        guardar_respondidos(usuarios_respondidos)  # Guardar inmediatamente
                        
                        print(f"[+] Lead procesado: {sender_id} - {numero_encontrado}")
                        
                    else:
                        # NO HAY NÚMERO: Verificar si ya se respondió antes
                        if sender_id not in usuarios_respondidos or not usuarios_respondidos[sender_id]:
                            # Solo responder si NO se ha respondido antes
                            responder_a_cliente(sender_id, "¡Gracias por contactarnos! Por favor comparte tu número telefónico para poder ayudarte mejor.")
                            usuarios_respondidos[sender_id] = True  # Ya respondió, no volverá a responder
                            guardar_respondidos(usuarios_respondidos)  # Guardar
                            print(f"[!] Se pidió el número a: {sender_id}")
                        else:
                            # Ya se respondió antes, no hacer nada
                            print(f"[!] Usuario {sender_id} ya recibió respuesta, ignorando mensaje sin número: {mensaje_texto[:30]}...")
                    # -----------------------
                    
    return "OK", 200

if __name__ == '__main__':
    # Cargar variables de entorno o pedirlas si no existen
    if not FACEBOOK_TOKEN:
        print("⚠️ ERROR: Configura FACEBOOK_PAGE_ACCESS_TOKEN en un archivo .env")
    if not VERIFY_TOKEN:
        print("⚠️ ERROR: Configura VERIFY_TOKEN en un archivo .env")
    
    print("🤖 Bot de Messenger iniciado...")
    app.run(port=5000, debug=True)
