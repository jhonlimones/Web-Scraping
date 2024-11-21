# Archivo de configuración para la conexión a la base de datos

import os

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '6328')
DB_NAME = os.getenv('DB_NAME', 'quotes_db')
