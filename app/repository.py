"""Repository layer for Document CRUD Service.
Encapsula la conexión a MongoDB usando la configuración del entorno.
"""
import os
from pymongo import MongoClient
from .core.config import MONGO_URI, MONGO_DB_NAME

class MongoRepository:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db["documentos"]

    # CRUD operations
    def obtener_por_checksum(self, checksum: str):
        return self.collection.find_one({"hash_seguridad": checksum}, {"_id": 0})

    def guardar_documento(self, archivo: str, texto: str, checksum: str):
        doc = {"archivo": archivo, "texto": texto, "hash_seguridad": checksum}
        return self.collection.insert_one(doc)

    def actualizar_nombre(self, checksum: str, nuevo_nombre: str):
        return self.collection.update_one({"hash_seguridad": checksum}, {"$set": {"archivo": nuevo_nombre}})

    def eliminar_documento(self, checksum: str):
        return self.collection.delete_one({"hash_seguridad": checksum})

    def listar_todos(self):
        return list(self.collection.find({}, {"_id": 0}))

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

