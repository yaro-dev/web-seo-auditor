from fpdf import FPDF
import os

class PDFPipeline:
    def __init__(self):
        self.data = None

    def process_item(self, item, spider):
        self.data = item
        return item

    def close_spider(self, spider):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(15, 15, 15)
            pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
            
            # Secciones mejoradas
            self._seccion_seo_mejorada(pdf)
            self._seccion_tecnica_mejorada(pdf)
            self._seccion_legibilidad(pdf)
            self._seccion_mejoras_mejorada(pdf)

            output_dir = "informes"
            os.makedirs(output_dir, exist_ok=True)
            pdf.output(f"{output_dir}/informe_seo.pdf")
            
        except Exception as e:
            print(f"Error generando PDF: {str(e)}")

    def _seccion_seo_mejorada(self, pdf):
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, "1. Elementos de SEO", 0, 1)
        
        # Datos existentes
        seo_data = [
            ("Título", self.data['seo']['titulo']),
            ("Meta Descripción", self.data['seo']['meta_descripcion']),
            ("Palabras Clave", self.data['seo']['palabras_clave']),
            ("URL", self.data['seo']['url'])
        ]
        
        # Nuevos datos sociales
        social = self.data['seo']['social_metadata']
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, "Redes Sociales:", 0, 1)
        pdf.set_font('DejaVu', '', 10)
        pdf.multi_cell(0, 8, f"OG Title: {social['og_title']}\nOG Image: {social['og_image']}\nTwitter Card: {social['twitter_card']}")
        
        # Resto de la sección
        pdf.set_font('DejaVu', '', 12)
        for label, value in seo_data:
            pdf.cell(50, 8, f"{label}:", 0, 0)
            pdf.multi_cell(0, 8, value or 'No encontrado')
            pdf.ln(5)

    def _seccion_tecnica_mejorada(self, pdf):
        pdf.add_page()
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, "2. Análisis Técnico", 0, 1)
        
        # ... (código existente)

        # Nueva sección con explicaciones
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, "Rendimiento (Core Web Vitals):", 0, 1)
        
        metricas = {
            'lcp': {
                'nombre': 'Largest Contentful Paint (LCP)',
                'desc': 'Tiempo de carga del elemento más grande visible en pantalla. Objetivo: < 2.5s'
            },
            'fid': {
                'nombre': 'First Input Delay (FID)',
                'desc': 'Tiempo hasta que la página responde a la primera interacción. Objetivo: < 100ms'
            },
            'cls': {
                'nombre': 'Cumulative Layout Shift (CLS)',
                'desc': 'Estabilidad visual durante la carga. Objetivo: < 0.1'
            }
        }

        pdf.set_font('DejaVu', '', 10)
        if 'error' in self.data['tecnico']['core_web_vitals']:
            pdf.multi_cell(0, 8, f"Error: {self.data['tecnico']['core_web_vitals']['error']}")
        else:
            cwv = self.data['tecnico']['core_web_vitals']
            for key in ['lcp', 'fid', 'cls']:
                # Nombre completo y valor
                pdf.set_font('', '', 10)
                pdf.multi_cell(0, 8, f"{metricas[key]['nombre']}: {cwv[key]}")
                
                # Descripción detallada
                pdf.set_font('', '', 8)
                pdf.multi_cell(0, 6, metricas[key]['desc'])
                pdf.ln(3)

    def _seccion_legibilidad(self, pdf):
        pdf.add_page()
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, "3. Legibilidad", 0, 1)
        
        legibilidad = self.data['legibilidad']
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(50, 8, "Puntaje:", 0, 0)
        pdf.cell(0, 8, str(legibilidad['puntaje']), 0, 1)
        pdf.ln(5)
        pdf.multi_cell(0, 8, "Interpretación: " + legibilidad['interpretacion'])

    def _seccion_mejoras_mejorada(self, pdf):
        pdf.add_page()
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, "4. Áreas de Mejora", 0, 1)
        
        # Nueva sección de indexabilidad
        index = self.data['mejoras']['indexabilidad']
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, "Indexabilidad:", 0, 1)
        pdf.set_font('DejaVu', '', 10)
        status = "X NO INDEXABLE" if index['noindex'] else "✓  INDEXABLE"
        bloqueos = "X Bloques detectados" if index['disallowed'] else "✓  Sin bloqueos"
        pdf.multi_cell(0, 8, f"Estado: {status}\n{bloqueos}")
        
        # Secciones originales
        categorias = {
            'SEO Técnico': self.data['mejoras']['seo_tecnico'],
            'Problemas en encabezados': self.data['mejoras']['problemas_encabezados'],
            'Oportunidades': self.data['mejoras']['oportunidades']
        }
        
        pdf.set_font('DejaVu', '', 12)
        for categoria, items in categorias.items():
            pdf.set_font('', '', 14)
            pdf.cell(0, 10, f"{categoria}:", 0, 1)
            pdf.set_font('', '', 12)
            
            if not items:
                pdf.cell(0, 8, "✓ Sin problemas detectados", 0, 1)
            else:
                for item in items:
                    pdf.cell(10)
                    pdf.multi_cell(0, 8, f"- {item}")
            pdf.ln(5)