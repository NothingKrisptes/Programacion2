from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import requests

class BibliotecaLibro (models.Model):
    _name = 'biblioteca.libro'
    _description = 'Modelo para gestionar libros en una biblioteca'
    _rec_name = 'nombre_libro'

    nombre_libro = fields.Char(string='Nombre del Libro')
    autor = fields.Many2one('biblioteca.autor', string='Autor')
    fecha_publicacion = fields.Date(string='Fecha de Publicación')
    isbn = fields.Char(string='ISBN')
    ejemplares_disponibles = fields.Integer(string='Ejemplares Disponibles', default=0)
    paginas = fields.Integer(string='Número de Páginas')
    genero = fields.Char(string='Género')
    descripcion = fields.Text(string='Descripción')
    costo = fields.Float(string='Costo')
    editorial = fields.Many2one('biblioteca.editorial', string='Editorial')


    def action_buscar_openlibrary(self):
     for record in self:
        if not record.nombre_libro:
            raise UserError("Por favor, ingrese el nombre del libro antes de buscar en OpenLibrary.")

        try:
            url = f"https://openlibrary.org/search.json?q={record.nombre_libro}&language=spa"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get('docs'):
                raise UserError("No se encontró ningún libro con ese nombre en OpenLibrary.")

            libro = data['docs'][0]
            work_key = libro.get('key')  # Ej: "/works/OL12345W"
            titulo = libro.get('title', 'Sin título')
            autor_nombre = libro.get('author_name', ['Desconocido'])[0]
            anio = libro.get('first_publish_year')
            editorial_nombre = libro.get('publisher', ['Desconocido'])[0]
            paginas = 0
            descripcion = ""
            generos = []
            isbn = libro.get('isbn', [None])[0] if libro.get('isbn') else None

            # Consultar datos adicionales desde works
            if work_key:
                work_url = f"https://openlibrary.org{work_key}.json"
                work_resp = requests.get(work_url, timeout=10)
                if work_resp.ok:
                    work_data = work_resp.json()

                    # Descripción
                    if isinstance(work_data.get('description'), dict):
                        descripcion = work_data['description'].get('value', '')
                    elif isinstance(work_data.get('description'), str):
                        descripcion = work_data['description']

                    # Géneros
                    if work_data.get('subjects'):
                        generos = work_data['subjects'][:3]

                    # Páginas, editorial e ISBN desde la primera edición
                    editions_url = f"https://openlibrary.org{work_key}/editions.json"
                    editions_resp = requests.get(editions_url, timeout=10)
                    if editions_resp.ok:
                        editions_data = editions_resp.json()
                        if editions_data.get('entries'):
                            entry = editions_data['entries'][0]
                            paginas = entry.get('number_of_pages', 0)
                            isbn = entry.get('isbn_10', [None])[0] if entry.get('isbn_10') else isbn
                            editorial_nombre = entry.get('publishers', [None])[0] if entry.get('publishers') else editorial_nombre

            # Buscar o crear autor
            autor = self.env['biblioteca.autor'].search([('seudonimo_autor', '=', autor_nombre)], limit=1)
            if not autor:
                autor = self.env['biblioteca.autor'].create({'seudonimo_autor': autor_nombre})

            # Buscar o crear editorial
            editorial = self.env['biblioteca.editorial'].search([('nombre_editorial', '=', editorial_nombre)], limit=1)
            if not editorial:
                editorial = self.env['biblioteca.editorial'].create({'nombre_editorial': editorial_nombre})

            # Manejo seguro de fecha
            fecha_publicacion = None
            if anio:
                if str(anio).isdigit() and len(str(anio)) == 4:
                    fecha_publicacion = f"{anio}-01-01"
                else:
                    # Si viene fecha completa, la usamos
                    fecha_publicacion = str(anio)

            # Rellenar campos
            record.write({
                'nombre_libro': titulo,
                'autor': autor.id,
                'isbn': isbn or "No disponible",
                'paginas': str(paginas) if paginas else "",
                'fecha_publicacion': fecha_publicacion,
                'descripcion': descripcion or "No hay descripción disponible.",
                'editorial': editorial.id,
                'genero': ", ".join(generos) if generos else "Desconocido",
            })

        except Exception as e:
            raise UserError(f"Error al conectar con OpenLibrary: {str(e)}")