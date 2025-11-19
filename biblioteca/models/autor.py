from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import requests

class BibliotecaAutor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'Modelo para gestionar autores en una biblioteca'
    _rec_name = 'seudonimo_autor'

    seudonimo_autor = fields.Char(string='Nombre del Autor')
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento')
    nacionalidad = fields.Char(string='Nacionalidad')
    biografia = fields.Text(string='Biografía')
    libros=fields.Many2many('biblioteca.libro', string='Libros Escritos')