import unittest
from scraper import QuoteScraper, DatabaseManager
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

class TestQuoteScraper(unittest.TestCase):
    def setUp(self):
        # Crear instancias simuladas de DatabaseManager y QuoteScraper
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.scraper = QuoteScraper(db_manager=self.mock_db_manager)

    def test_clean_text(self):
        text = '“La vida es bella”'
        cleaned = self.scraper.clean_text(text)
        self.assertEqual(cleaned, 'La vida es bella')

    def test_clean_author(self):
        author = ' Albert Einstein '
        cleaned = self.scraper.clean_author(author)
        self.assertEqual(cleaned, 'Albert Einstein')

    def test_clean_tags(self):
        tags = [' life ', ' inspirational ']
        cleaned = self.scraper.clean_tags(tags)
        self.assertEqual(cleaned, ['life', 'inspirational'])

    def test_clean_born_date(self):
        date = ' March 14, 1879 '
        cleaned = self.scraper.clean_born_date(date)
        self.assertEqual(cleaned, 'March 14, 1879')

    def test_clean_born_location(self):
        location = ' Ulm, Germany '
        cleaned = self.scraper.clean_born_location(location)
        self.assertEqual(cleaned, 'Ulm, Germany')

    @patch('scraper.requests.get')
    def test_get_author_info(self, mock_get):
        # Simular la respuesta de requests.get
        mock_response = MagicMock()
        mock_response.text = '''
        <html>
            <span class="author-born-date">January 1, 1900</span>
            <span class="author-born-location">Somewhere</span>
            <div class="author-description">An amazing author.</div>
        </html>
        '''
        mock_get.return_value = mock_response

        author_info = self.scraper.get_author_info('http://example.com/author')
        expected_info = {
            'born_date': 'January 1, 1900',
            'born_location': 'Somewhere',
            'description': 'An amazing author.'
        }
        self.assertEqual(author_info, expected_info)

    @patch('scraper.requests.get')
    def test_process_quote(self, mock_get):
        # Simular el contenido de una cita
        quote_html = '''
        <div class="quote">
            <span class="text">“Test quote”</span>
            <small class="author">Test Author</small>
            <a href="/author/Test-Author">(about)</a>
            <div class="tags">
                <a class="tag">test</a>
                <a class="tag">sample</a>
            </div>
        </div>
        '''
        soup = BeautifulSoup(quote_html, 'html.parser')
        quote = soup.find('div', class_='quote')

        # Simular la respuesta de get_author_info
        self.scraper.get_author_info = MagicMock(return_value={
            'born_date': 'January 1, 1900',
            'born_location': 'Somewhere',
            'description': 'An amazing author.'
        })

        # Ejecutar el método
        self.scraper.process_quote(quote)

        # Verificar que se llamaron los métodos de DatabaseManager
        self.assertTrue(self.mock_db_manager.insert_author.called)
        self.assertTrue(self.mock_db_manager.insert_quote.called)
        self.assertTrue(self.mock_db_manager.insert_tag.called)
        self.assertTrue(self.mock_db_manager.insert_quote_tag.called)

if __name__ == '__main__':
    unittest.main()
