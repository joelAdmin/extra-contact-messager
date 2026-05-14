# 2. Pegar este código en el archivo
from pymongo import MongoClient

# Tu URI completa (la que usaste antes)
uri = "mongodb+srv://jlama1411_db_user:3CL2ymM8qLAetqiQ@clusterbotfacebookmessa.exakdfr.mongodb.net/"
client = MongoClient(uri)
db = client['plataforma_bots']

print("✅ Conexión exitosa!")
print("Colecciones:", db.list_collection_names())
print("Clientes:", db.clients.count_documents({}))
print("Contactos:", db.contacts.count_documents({}))
