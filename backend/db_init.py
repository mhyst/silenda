#!/usr/bin/env python
import sqlite3
from datetime import datetime

# Conexión a la base de datos (se crea si no existe)
conn = sqlite3.connect("mensajeria.db")
cursor = conn.cursor()

# Crear tabla de usuarios
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    clave TEXT NOT NULL,
    fecha_creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT 1
);
""")

# Crear tabla de salas
cursor.execute("""
CREATE TABLE IF NOT EXISTS salas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    privada BOOLEAN NOT NULL DEFAULT 1,
    fecha_creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

# Crear tabla intermedia usuarios_salas
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios_salas (
    usuario_id INTEGER NOT NULL,
    sala_id INTEGER NOT NULL,
    rol TEXT DEFAULT 'miembro',
    fecha_union TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, sala_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (sala_id) REFERENCES salas(id)
);
""")

# Crear tabla de mensajes
cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sala_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    contenido TEXT NOT NULL,
    fecha_envio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sala_id) REFERENCES salas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
""")

# Confirmar cambios y cerrar conexión
conn.commit()
conn.close()

print("Base de datos creada correctamente.")

