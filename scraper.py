import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import logging
import schedule
import time
import config

# Configuración del sistema de logs
logging.basicConfig(
    level=logging.INFO,  # Nivel mínimo de mensajes a registrar
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),  # Archivo donde se guardarán los logs
        logging.StreamHandler()  # También muestra los logs en la consola
    ]
)
class DatabaseManager:
    """Clase para manejar la conexión y operaciones con la base de datos."""
    def __init__(self):
        self.connection = self.create_connection()
        if self.connection:
            self.cursor = self.connection.cursor(buffered=True)
        else:
            self.cursor = None

    def create_connection(self):
        """Crea una conexión a la base de datos MySQL."""
        try:
            connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            if connection.is_connected():
                logging.info("Conexión exitosa a la base de datos MySQL")
                return connection
        except Error as e:
            logging.error(f"Error al conectar a MySQL: {e}")
            return None

    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logging.info("Conexión a la base de datos cerrada.")

    def insert_author(self, author_data):
        """Inserta un autor en la base de datos o devuelve su ID si ya existe."""
        try:
            self.cursor.execute("SELECT id FROM authors WHERE name = %s", (author_data['name'],))
            result = self.cursor.fetchone()
            if result:
                logging.debug(f"Autor '{author_data['name']}' ya existe en la base de datos.")
                return result[0]
            else:
                self.cursor.execute("""
                    INSERT INTO authors (name, born_date, born_location, description)
                    VALUES (%s, %s, %s, %s)
                """, (author_data['name'], author_data['born_date'], author_data['born_location'], author_data['description']))
                self.connection.commit()
                logging.info(f"Autor '{author_data['name']}' insertado en la base de datos.")
                return self.cursor.lastrowid
        except Error as e:
            logging.error(f"Error al insertar autor '{author_data['name']}': {e}")
            return None

    def insert_quote(self, quote_text, author_id):
        """Inserta una cita en la base de datos."""
        try:
            self.cursor.execute("INSERT INTO quotes (author_id, quote) VALUES (%s, %s)", (author_id, quote_text))
            self.connection.commit()
            logging.info(f"Cita insertada: '{quote_text[:50]}...'")
            return self.cursor.lastrowid
        except Error as e:
            logging.error(f"Error al insertar cita: {e}")
            return None

    def insert_tag(self, tag):
        """Inserta una etiqueta en la base de datos o devuelve su ID si ya existe."""
        try:
            self.cursor.execute("SELECT id FROM tags WHERE tag = %s", (tag,))
            result = self.cursor.fetchone()
            if result:
                logging.debug(f"Tag '{tag}' ya existe en la base de datos.")
                return result[0]
            else:
                self.cursor.execute("INSERT INTO tags (tag) VALUES (%s)", (tag,))
                self.connection.commit()
                logging.info(f"Tag '{tag}' insertado en la base de datos.")
                return self.cursor.lastrowid
        except Error as e:
            logging.error(f"Error al insertar tag '{tag}': {e}")
            return None

    def insert_quote_tag(self, quote_id, tag_id):
        """Inserta la relación entre una cita y una etiqueta."""
        try:
            self.cursor.execute("INSERT INTO quote_tags (quote_id, tag_id) VALUES (%s, %s)", (quote_id, tag_id))
            self.connection.commit()
            logging.debug(f"Relación cita-tag insertada: cita_id={quote_id}, tag_id={tag_id}")
        except Error as e:
            logging.error(f"Error al insertar relación cita-tag: {e}")

class QuoteScraper:
    """Clase para extraer y procesar las citas desde el sitio web."""
    BASE_URL = 'http://quotes.toscrape.com'

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def scrape(self):
        """Inicia el proceso de scraping."""
        page = 1
        logging.info("Inicio del proceso de scraping.")

        while True:
            try:
                response = requests.get(f'{self.BASE_URL}/page/{page}/')
                if response.status_code != 200:
                    logging.warning(f"Página {page} no encontrada (Status code: {response.status_code})")
                    break
                soup = BeautifulSoup(response.text, 'html.parser')

                quotes = soup.find_all('div', class_='quote')

                if not quotes:
                    logging.info(f"No se encontraron más citas en la página {page}. Fin del scraping.")
                    break

                logging.info(f"Procesando página {page} con {len(quotes)} citas.")

                for quote in quotes:
                    try:
                        self.process_quote(quote)
                    except Exception as e:
                        logging.error(f"Error al procesar la cita: {e}")
                        continue

                logging.info(f"Página {page} procesada exitosamente.")
                page += 1
            except Exception as e:
                logging.error(f"Error al procesar la página {page}: {e}")
                break

        logging.info("Proceso de scraping completado.")

    def process_quote(self, quote):
        """Procesa una sola cita."""
        # Extracción de datos
        text = quote.find('span', class_='text').get_text()
        author_name = quote.find('small', class_='author').get_text()
        tags = [tag.get_text() for tag in quote.find_all('a', class_='tag')]
        author_url = self.BASE_URL + quote.find('a')['href']

        # Limpieza de datos
        text = self.clean_text(text)
        author_name = self.clean_author(author_name)
        tags = self.clean_tags(tags)

        # Obtener información adicional del autor
        author_data = self.get_author_info(author_url)
        author_data['name'] = author_name

        # Insertar datos en la base de datos
        author_id = self.db_manager.insert_author(author_data)
        if author_id is None:
            return

        quote_id = self.db_manager.insert_quote(text, author_id)
        if quote_id is None:
            return

        for tag in tags:
            tag_id = self.db_manager.insert_tag(tag)
            if tag_id is not None:
                self.db_manager.insert_quote_tag(quote_id, tag_id)

    def get_author_info(self, url):
        """Obtiene información adicional del autor desde su página."""
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        born_date = soup.find('span', class_='author-born-date').get_text()
        born_location = soup.find('span', class_='author-born-location').get_text()
        description = soup.find('div', class_='author-description').get_text().strip()

        # Limpieza de datos
        born_date = self.clean_born_date(born_date)
        born_location = self.clean_born_location(born_location)

        return {
            'born_date': born_date,
            'born_location': born_location,
            'description': description
        }

    # Funciones de limpieza
    @staticmethod
    def clean_text(text):
        return text.replace('“', '').replace('”', '').strip()

    @staticmethod
    def clean_author(author):
        return author.strip()

    @staticmethod
    def clean_tags(tags):
        return [tag.strip().lower() for tag in tags]

    @staticmethod
    def clean_born_date(date):
        return date.strip()

    @staticmethod
    def clean_born_location(location):
        return location.strip()

def run_scraper():
    """Función para ejecutar el scraper."""
    db_manager = DatabaseManager()
    if db_manager.connection is None:
        logging.error("No se pudo establecer la conexión con la base de datos.")
        return

    scraper = QuoteScraper(db_manager)
    scraper.scrape()
    db_manager.close_connection()

def schedule_scraping():
    """Programa la ejecución del scraper cada día a las 00:00."""
    schedule.every().day.at("00:00").do(run_scraper)
    logging.info("Scraper programado para ejecutarse todos los días a las 00:00.")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Ejecutar el scraper una vez
    run_scraper()

    # Descomenta la siguiente línea para programar el scraping diario
    # threading.Thread(target=schedule_scraping).start()
