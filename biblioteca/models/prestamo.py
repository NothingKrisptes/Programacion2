from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class BibliotecaPrestamo(models.Model):
    _name = 'biblioteca.prestamo'
    _description = 'Modelo para gestionar préstamos de libros en una biblioteca'
    _rec_name = 'usuario'

    name = fields.Char(string="Código de Préstamo")
    usuario = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
    libro = fields.Many2one('biblioteca.libro', string='Libro', required=True)
    fecha_prestamo = fields.Date(string='Fecha de Préstamo', default=fields.Date.context_today, required=True)
    fecha_devolucion = fields.Date(string='Fecha de Devolución')
    libros_prestados = fields.Many2many('biblioteca.libro', string='Libros Prestados')
    fecha_maxima = fields.Date(string='Fecha Máxima de Devolución', compute='_compute_fecha_devolucion', store=True)
    estado = fields.Selection([
        ('b', 'Borrador'),
        ('p', 'Prestado'),
        ('d', 'Devuelto'),
        ('m', 'Multado')
    ], string='Estado', default='b', required=True)
    evaluacion_libro = fields.Selection([
        ('b', 'Buen estado'),
        ('d', 'Deteriorado/Dañado'),
        ('p', 'Perdida Total')
    ], string='Evaluación del Libro',default='b')
    # Campo computado para saber si tiene multas
    tiene_multas = fields.Boolean(compute='_compute_tiene_multas', store=True)
    total_multas = fields.Float(compute='_compute_total_multas', string='Total Multas ($)')
    multa_ids = fields.One2many('biblioteca.multa', 'prestamo', string='Multas Generadas')
    devolucion_tardia = fields.Boolean(string='Devolución Tardía', default=False)

    @api.constrains('fecha_prestamo', 'fecha_devolucion')
    def _check_fechas(self):
        for record in self:
            if record.fecha_prestamo and record.fecha_devolucion and record.fecha_devolucion <= record.fecha_prestamo:
                raise ValidationError("La fecha de devolución debe ser posterior a la fecha de préstamo.")
            
    @api.depends('fecha_prestamo', 'fecha_maxima')
    def _compute_fecha_devolucion(self):
        for record in self:
            if record.fecha_prestamo:
                record.fecha_maxima = record.fecha_prestamo + timedelta(days=7)
            else:
                record.fecha_maxima = False

    def write(self, vals):
        seq = self.env.ref('biblioteca.sequence_codigo_prestamos').next_by_code('biblioteca.prestamo')
        vals['name'] = seq
        return super(BibliotecaPrestamo, self).write(vals)
    
    @api.depends('multa_ids')
    def _compute_tiene_multas(self):
        for record in self:
            record.tiene_multas = len(record.multa_ids) > 0
    
    @api.depends('multa_ids.monto')
    def _compute_total_multas(self):
        for record in self:
            record.total_multas = sum(record.multa_ids.mapped('monto'))

    def _cron_multas(self):
        """Cron que verifica préstamos vencidos y crea multas por retraso automáticamente"""
        ahora = fields.Datetime.now()
        prestamos = self.env['biblioteca.prestamo'].search([
            ('estado', '=', 'p'),
            ('fecha_maxima', '<', ahora),
        ])

        for prestamo in prestamos:
            multa_retraso = self.env['biblioteca.multa'].search([
            ('prestamo', '=', prestamo.id),
            ('tipo_multa', '=', 'retraso'),
            ], limit=1)

            if prestamo.fecha_maxima:
                days = (ahora.date() - prestamo.fecha_maxima).days
            else:
                days = 0

            if days <= 0:
                continue

            if not multa_retraso:
                prestamo._crear_multa('retraso', days * 1.0)
            else:
                multa_retraso.write({'monto': days * 1.0})

    def generar_prestamo(self):
        print("Generando préstamo")
        if self.libro.ejemplares_disponibles <= 0:
            raise UserError('❌ No hay ejemplares disponibles para este libro.')
        self.libro.ejemplares_disponibles -= 1
        self.write({'estado': 'p'})

    def _crear_multa(self, tipo_multa, costo):
        """Método auxiliar para crear multas"""
        self.ensure_one()
        seq = self.env.ref('biblioteca.sequence_codigo_multa').next_by_code('biblioteca.multa')

        descripciones = {
            'retraso': f"Multa por retraso en la devolución del libro '{self.libro.nombre_libro}'",
            'deterioro': f"Multa por deterioro del libro '{self.libro.nombre_libro}'",
            'perdida': f"Multa por pérdida del libro '{self.libro.nombre_libro}'",
         }

        self.env['biblioteca.multa'].create({
            'nombre_multa': seq,
            'descripcion_multa': descripciones.get(tipo_multa, 'Multa'),
            'monto': costo,
            'fecha_multa': fields.Date.context_today(self),
            'prestamo': self.id,
            'tipo_multa': tipo_multa,
            'usuario': self.usuario.id,
        })

        if self.estado == 'p':
            self.write({'estado': 'm'})

    def action_devolver(self):
        """Acción de devolución con generación automática de multas"""
        if self.estado not in ['p', 'm']:  # ← Agregar 'm' aquí
            raise UserError('❌ Solo se pueden devolver préstamos en estado "Prestado" o "Multado"')
        
        fecha_actual = datetime.now()
        
        # 1. MULTA POR PÉRDIDA (Solo esta, cancela las demás)
        if self.evaluacion_libro == 'p':
            # Eliminar otras multas si existen
            self.multa_ids.unlink()
            
            # Crear multa por pérdida (costo del libro x 2)
            costo_perdida = (self.libro.costo or 20.0) * 2
            self._crear_multa('p', costo_perdida)
            
            self.write({
                'estado': 'd',
                'fecha_devolucion': fecha_actual
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Libro Perdido',
                    'message': f'Se ha registrado la pérdida del libro. Multa: ${costo_perdida:.2f}',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # 2. MULTA POR DAÑO
        if self.evaluacion_libro == 'd':
            # Verificar si ya existe multa por daño
            multa_dano = self.env['biblioteca.multa'].search([
                ('prestamo', '=', self.id),
                ('tipo_multa', '=', 'deterioro')
            ])
            
            if not multa_dano:
                costo_dano = (self.libro.costo or 20.0) * 0.5
                self._crear_multa('deterioro', costo_dano)
        
        # 3. MULTA POR RETRASO
        es_tarde = self.devolucion_tardia or (self.fecha_maxima and fecha_actual.date() > self.fecha_maxima)
        
        if es_tarde:
            # Verificar si ya existe multa por retraso
            multa_retraso = self.env['biblioteca.multa'].search([
                ('prestamo', '=', self.id),
                ('tipo_multa', '=', 'retraso')
            ])
            
            if self.fecha_maxima and fecha_actual.date() > self.fecha_maxima:
                days = (fecha_actual.date() - self.fecha_maxima).days
            else:
                days = 1
            
            if not multa_retraso:
                self._crear_multa('retraso', days * 1.0)
            else:
                # Actualizar la multa existente
                multa_retraso.write({'monto': days * 1.0})
        
        # Actualizar estado del préstamo
        self.write({
            'estado': 'd',
            'fecha_devolucion': fecha_actual
        })
        
        # Mensaje de confirmación
        total = self.total_multas
        if total > 0:
            mensaje = f'Libro devuelto. Total multas: ${total:.2f}'
            tipo = 'warning'
        else:
            mensaje = f'El libro "{self.libro.nombre_libro}" ha sido devuelto exitosamente sin multas.'
            tipo = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Libro Devuelto',
                'message': mensaje,
                'type': tipo,
                'sticky': False,
            }
        }