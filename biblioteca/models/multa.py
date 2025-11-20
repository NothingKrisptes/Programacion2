from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class BibliotecaMulta(models.Model):
    _name = 'biblioteca.multa'
    _description = 'Modelo para gestionar multas por retrasos en la devolución de libros'
    _rec_name = 'prestamo'

    prestamo = fields.Many2one('biblioteca.prestamo', string='Préstamo', required=True)
    usuario = fields.Many2one(related='prestamo.usuario', string='Usuario', store=True)
    libro = fields.Many2one(related='prestamo.libro', string='Libro', store=True)
    fecha_multa = fields.Date(string='Fecha de Multa', default=fields.Date.context_today, required=True)
    monto = fields.Float(string='Monto de la Multa', required=True)
    pagado = fields.Boolean(string='Pagado', default=False)

    @api.constrains('prestamo')
    def _check_prestamo_retrasado(self):
        for record in self:
            if record.prestamo and record.prestamo.estado != 'retrasado':
             raise ValidationError("La multa solo puede ser creada para préstamos con estado 'Retrasado'.")