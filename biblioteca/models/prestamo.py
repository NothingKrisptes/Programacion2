from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class BibliotecaPrestamo(models.Model):
    _name = 'biblioteca.prestamo'
    _description = 'Modelo para gestionar préstamos de libros en una biblioteca'
    _rec_name = 'usuario'

    usuario = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
    libro = fields.Many2one('biblioteca.libro', string='Libro', required=True)
    fecha_prestamo = fields.Date(string='Fecha de Préstamo', default=fields.Date.context_today, required=True)
    fecha_devolucion = fields.Date(string='Fecha de Devolución', required=True)
    estado = fields.Selection([
        ('prestado', 'Prestado'),
        ('devuelto', 'Devuelto'),
        ('retrasado', 'Retrasado')
    ], string='Estado', default='prestado', required=True)

    @api.model
    def create(self, vals):
        if 'fecha_devolucion' in vals and vals['fecha_devolucion'] <= fields.Date.context_today(self):
            raise ValidationError("La fecha de devolución debe ser posterior a la fecha de préstamo.")
        return super(BibliotecaPrestamo, self).create(vals)