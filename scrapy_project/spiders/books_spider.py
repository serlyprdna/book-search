import scrapy
import json
import os

class BooksSpider(scrapy.Spider):
    name = 'books'
    allowed_domains = ['books.toscrape.com']
    start_urls = ['https://books.toscrape.com/']
    
    def parse(self, response):
        # Mengambil semua link buku dari halaman
        books = response.css('article.product_pod')
        
        for book in books:
            book_url = book.css('h3 a::attr(href)').get()
            if book_url:
                # Membuat URL lengkap untuk setiap buku
                book_url = response.urljoin(book_url)
                yield scrapy.Request(book_url, callback=self.parse_book)
        
        # Mengikuti pagination untuk halaman berikutnya
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse)
    
    def parse_book(self, response):
        # Mengambil informasi detail dari setiap buku
        title = response.css('h1::text').get()
        price = response.css('p.price_color::text').get()
        availability = response.css('p.availability::text').re_first(r'In stock \((\d+) available\)')
        
        # Mengambil rating buku
        rating_class = response.css('p.star-rating::attr(class)').get()
        rating_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        rating = 0
        if rating_class:
            for word in rating_class.split():
                if word in rating_map:
                    rating = rating_map[word]
                    break
        
        # Mengambil deskripsi buku
        description = response.css('div#product_description + p::text').get()
        if not description:
            description = "No description available"
        
        # Mengambil kategori
        category = response.css('ul.breadcrumb li:nth-child(3) a::text').get()
        
        # Mengambil informasi tambahan dari tabel
        product_info = {}
        table_rows = response.css('table.table-striped tr')
        for row in table_rows:
            key = row.css('td:first-child::text').get()
            value = row.css('td:last-child::text').get()
            if key and value:
                product_info[key] = value
        
        # Mengambil URL gambar
        image_url = response.css('div.item.active img::attr(src)').get()
        if image_url:
            image_url = response.urljoin(image_url)
        
        yield {
            'title': title.strip() if title else '',
            'price': price.strip() if price else '',
            'availability': availability if availability else '0',
            'rating': rating,
            'description': description.strip() if description else '',
            'category': category.strip() if category else '',
            'image_url': image_url,
            'upc': product_info.get('UPC', ''),
            'product_type': product_info.get('Product Type', ''),
            'tax': product_info.get('Tax', ''),
            'number_of_reviews': product_info.get('Number of reviews', '0'),
            'url': response.url
        }
    
    def closed(self, reason):
        # Membuat folder data jika belum ada
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.logger.info(f'Spider closed: {reason}')
