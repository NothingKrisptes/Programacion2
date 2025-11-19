from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import requests

class BibliotecaLibro (models.Model):
    _name = 'biblioteca.libro'
    _description = 'Modelo para gestionar libros en una biblioteca'
    _rec_name = 'nombre_libro'

    nombre_libro = fields.Char(string='Nombre del Libro')
    autor = fields.Char(string='Autor')
    fecha_publicacion = fields.Date(string='Fecha de Publicación')
    isbn = fields.Char(string='ISBN')
    ejemplares_disponibles = fields.Integer(string='Ejemplares Disponibles', default=0)
    paginas = fields.Integer(string='Número de Páginas')
    genero = fields.Selection([
        ('ficcion', 'Ficción'),
        ('no_ficcion', 'No Ficción'),
        ('ciencia', 'Ciencia'),
        ('historia', 'Historia'),
        ('fantasia', 'Fantasía'),
        ('biografia', 'Biografía')
    ], string='Género')
    descripcion = fields.Text(string='Descripción')
    costo = fields.Float(string='Costo')
    editorial = fields.Char(string='Editorial')

