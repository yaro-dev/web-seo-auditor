import scrapy
from urllib.parse import urlparse, urljoin
from scrapy.http import Request
from scrapy.spidermiddlewares.httperror import HttpError
import re
import hashlib
import requests  

class SEOSpider(scrapy.Spider):
    name = "seo_spider"
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'HTTPERROR_ALLOW_ALL': False,
        'AUTOTHROTTLE_ENABLED': True
    }

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.base_url = urlparse(url).geturl()
        self.results = {
            'seo': {
                'titulo': '',
                'meta_descripcion': '',
                'palabras_clave': '',
                'url': url,
                'social_metadata': {}  
            },
            'tecnico': {
                'servidor': '',
                'tecnologia': '',
                'frameworks': [],
                'core_web_vitals': {}, 
                'duplicate_content': ''  
            },
            'legibilidad': {
                'puntaje': 0,
                'interpretacion': ''
            },
            'mejoras': {
                'seo_tecnico': [],
                'problemas_encabezados': [],
                'oportunidades': [],
                'indexabilidad': {}  
            }
        }
        self.content_hashes = {}

    def parse(self, response):
        # Funcionalidades existentes
        self._parse_seo(response)
        self._parse_tecnico(response)
        self._calc_legibilidad(response)
        self._detectar_problemas(response)
        
        # Nuevas funcionalidades añadidas
        self._check_social_metadata(response)
        self._check_indexability(response)
        self._check_duplicate_content(response)
        self._get_pagespeed_metrics(response.url)
        
        yield self.results

    # Métodos existentes 
    def _parse_seo(self, response):
        self.results['seo'].update({
            'titulo': response.xpath('//title/text()').get('').strip(),
            'meta_descripcion': response.xpath('//meta[@name="description"]/@content').get('')[:160],
            'palabras_clave': ', '.join(response.xpath('//meta[@name="keywords"]/@content').getall())
        })

    def _parse_tecnico(self, response):
        self.results['tecnico'].update({
            'servidor': response.headers.get('Server', b'').decode('utf-8', 'ignore'),
            'tecnologia': response.headers.get('X-Powered-By', b'').decode('utf-8', 'ignore'),
            'frameworks': self._detectar_frameworks(response)
        })

    def _detectar_frameworks(self, response):
        frameworks = []
        if response.xpath('//meta[@name="generator" and contains(@content, "WordPress")]'):
            frameworks.append('WordPress')
        if response.xpath('//script[contains(@src, "react")]'):
            frameworks.append('React')
        if response.xpath('//meta[@name="shopify-checkout-api-token"]'):
            frameworks.append('Shopify')
        return frameworks

    def _calc_legibilidad(self, response):
        text = ' '.join(response.xpath('''
            //body//*[not(self::script|self::style|self::noscript)]/text()
        ''').getall())
        
        words = [w for w in re.findall(r'\b\w+\b', text) if len(w) > 3]
        sentences = re.split(r'[.!?]+', text)
        syllables = sum(len(re.findall(r'[aeiouáéíóú]', word, re.IGNORECASE)) for word in words)
        
        if len(words) > 10 and len(sentences) > 1:
            score = 206.835 - (1.015 * (len(words)/len(sentences))) - (84.6 * (syllables/len(words)))
            self.results['legibilidad']['puntaje'] = round(score, 1)
            self.results['legibilidad']['interpretacion'] = self._interpretar_legibilidad(score)

    def _interpretar_legibilidad(self, score):
        if score < 30: return "Muy complejo (universitario)"
        if score < 60: return "Moderadamente difícil (bachillerato)"
        if score < 80: return "Fácil (12-15 años)"
        return "Muy fácil (niños)"

    def _detectar_problemas(self, response):
        self._check_h1_structure(response)
        self._check_links(response)
        self._analizar_encabezados(response)

    def _check_h1_structure(self, response):
        h1s = response.xpath('//h1//text()').getall()
        if len(h1s) != 1:
            self.results['mejoras']['seo_tecnico'].append(
                f"Problema H1: {'Demasiados H1s' if len(h1s) > 1 else 'H1 faltante'}"
            )

    def _analizar_encabezados(self, response):
        niveles = []
        for header in response.xpath('//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'):
            nivel = int(header.xpath('name()').get()[1])
            niveles.append(nivel)
        
        if not self._estructura_valida(niveles):
            self.results['mejoras']['problemas_encabezados'].append(
                "Estructura jerárquica incorrecta"
            )

    def _estructura_valida(self, niveles):
        last = 0
        for n in niveles:
            if n > last + 1:
                return False
            last = n
        return True

    def _check_links(self, response):
        for link in response.xpath('//a/@href').getall():
            full_url = urljoin(response.url, link)
            if not self._es_url_valida(full_url):
                self.results['mejoras']['oportunidades'].append(
                    f"Enlace no HTTP: {link}"
                )

    def _es_url_valida(self, url):
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https']

    # Nuevos métodos añadidos
    def _check_social_metadata(self, response):
        """ Verifica metatags para redes sociales """
        self.results['seo']['social_metadata'] = {
            'og_title': response.xpath('//meta[@property="og:title"]/@content').get(),
            'og_image': response.xpath('//meta[@property="og:image"]/@content').get(),
            'twitter_card': '✓' if response.xpath('//meta[@name="twitter:card"]') else 'X'
        }

    def _check_indexability(self, response):
        """ Verifica si la página es indexable """
        self.results['mejoras']['indexabilidad'] = {
            'noindex': 'noindex' in response.xpath('//meta[@name="robots"]/@content').get('').lower(),
            'disallowed': any(p in response.url for p in ['/admin', '/private', '/test'])
        }

    def _check_duplicate_content(self, response):
        """ Detección de contenido duplicado """
        content_hash = hashlib.md5(response.text.encode()).hexdigest()
        if content_hash in self.content_hashes:
            self.results['tecnico']['duplicate_content'] = f"(!) Duplicado con: {self.content_hashes[content_hash]}"
        else:
            self.content_hashes[content_hash] = response.url
            self.results['tecnico']['duplicate_content'] = "✓ Contenido único"

    def _get_pagespeed_metrics(self, url):
        """ Obtiene métricas de rendimiento """
        try:
            api_key = ""  # Obtener en: https://developers.google.com/speed/docs/insights/v5/get-started
            api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
            data = requests.get(api_url).json()
            
            self.results['tecnico']['core_web_vitals'] = {
                'lcp': data['lighthouseResult']['audits']['largest-contentful-paint']['displayValue'],
                'fid': data['lighthouseResult']['audits']['max-potential-fid']['displayValue'],
                'cls': data['lighthouseResult']['audits']['cumulative-layout-shift']['displayValue']
            }
        except Exception as e:
            self.results['tecnico']['core_web_vitals'] = {'error': str(e)}