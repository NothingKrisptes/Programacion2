from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import requests

class BibliotecaEditorial(models.Model):
    _name = 'biblioteca.editorial'
    _description = 'Modelo para gestionar editoriales en una biblioteca'
    _rec_name = 'nombre_editorial'

    nombre_editorial = fields.Char(string='Nombre de la Editorial', required=True)
    direccion = fields.Char(string='Dirección', default='')
    telefono = fields.Char(string='Teléfono', default='')
    email = fields.Char(string='Correo Electrónico', default='')
    pais = fields.Char(string='País', default='')
    libros_publicados = fields.One2many('biblioteca.libro', 'editorial', string='Libros Publicados')