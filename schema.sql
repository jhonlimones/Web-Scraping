-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS quotes_db;
USE quotes_db;

-- Tabla de autores
CREATE TABLE IF NOT EXISTS authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    born_date VARCHAR(255),
    born_location VARCHAR(255),
    description TEXT
);

-- Tabla de citas
CREATE TABLE IF NOT EXISTS quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author_id INT,
    quote TEXT,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- Tabla de etiquetas
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag VARCHAR(255) UNIQUE
);

-- Tabla de relación entre citas y etiquetas
CREATE TABLE IF NOT EXISTS quote_tags (
    quote_id INT,
    tag_id INT,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
