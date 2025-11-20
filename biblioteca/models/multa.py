from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class BibliotecaMulta(models.Model):
    _name = 'biblioteca.multa'
    _description = 'Modelo para gestionar multas por retrasos en la devolución de libros'
    _rec_name = 'prestamo'

    nombre_multa = fields.Char(string='Código de Multa', readonly=True)
    fecha_multa = fields.Date(string='Fecha de Multa', default=fields.Date.context_today, required=True)
    monto = fields.Float(string='Monto de la Multa', required=True)
    descripcion_multa = fields.Char(string='Descripción de la Multa')
    
    # RELACIÓN MANY2ONE: Una multa pertenece a UN SOLO préstamo
    prestamo = fields.Many2one('biblioteca.prestamo', string='Préstamo', required=True, ondelete='cascade')

    # Relación con usuario (para facilitar consultas)
    usuario = fields.Many2one('biblioteca.usuario', string='Usuario Multado', store=True)

    tipo_multa = fields.Selection([
        ('retraso', 'Retraso en Devolución'),
        ('deterioro', 'Deterioro/Daños'),
        ('perdida', 'Pérdida Total del Libro')
    ], string='Tipo de Multa', required=True)

    pagado = fields.Boolean(string='Pagado', default=False)
