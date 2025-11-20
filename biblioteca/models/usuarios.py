from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools.mail import email_re

class BibliotecaUsuario(models.Model):
    _name = 'biblioteca.usuario'
    _description = 'biblioteca.usuario'
    _rec_name = 'nombre_usuario'

    nombre_usuario = fields.Char(string='Nombre', required=True)
    apellido_usuario = fields.Char(string='Apellido', required=True)
    cedula_usuario = fields.Char(string='CI o Cédula', required=True)
    usuario_telefono = fields.Char(string='Celular', required=True)
    usuario_direccion = fields.Char(string='Dirección', required=True)
    usuario_mail = fields.Char(string='Correo electrónico', required=True)
    id_usuario = fields.Many2one('res.partner', string='Cliente Odoo')

    @api.onchange('id_usuario')
    def _onchange_usuario_id(self):
        if self.id_usuario:
            partner = self.id_usuario
            self.nombre_usuario = partner.name or ""
            if partner.name and " " in partner.name:
                    partes = partner.name.split(" ", 1)
                    self.nombre_usuario = partes[0]
                    self.apellido_usuario = partes[1]
            else:
                self.apellido_usuario = ""
            self.usuario_mail = partner.email or ""
            self.usuario_telefono = partner.phone or ""
            self.usuario_direccion = partner.street or ""
        else:
            self.nombre_usuario = ""
            self.apellido_usuario = ""
            self.usuario_mail = ""
            self.usuario_telefono = ""
            self.usuario_direccion = ""

    @api.constrains('cedula_usuario')
    def _check_cedula(self):
        for record in self:
            if record.cedula_usuario and not self.validar_cedula_ec(record.cedula_usuario):
                raise ValidationError("Cédula ecuatoriana inválida: %s" % record.cedula_usuario)
    def validar_cedula_ec(self, cedula):
        if len(cedula) != 10 or not cedula.isdigit():
            return False

        provincia = int(cedula[0:2])
        if provincia < 1 or provincia > 24:
            return False

        coef = [2,1,2,1,2,1,2,1,2]
        total = 0
        for i in range(9):
            val = int(cedula[i]) * coef[i]
            if val >= 10:
                val -= 9
            total += val
        digito_verificador = 10 - (total % 10) if total % 10 != 0 else 0
        return digito_verificador == int(cedula[9])

    @api.constrains('usuario_mail')
    def _check_valid_mail(self):
        for record in self:
            if record.usuario_mail and not email_re.match(record.usuario_mail):
                raise ValidationError("El formato del correo electrónico no es el correcto.")
    
    @api.constrains('cedula_usuario','usuario_mail')
    def _check_unique_usuario(self):
        for record in self:
            if self.search_count([('cedula_usuario', '=', record.cedula_usuario), ('id', '!=', record.id)]) > 0:
                raise ValidationError('La cédula ya está registrada en otro usuario.')
            if self.search_count([('usuario_mail', '=', record.usuario_mail), ('id', '!=', record.id)]) > 0:
                raise ValidationError('El correo electrónico ya está registrado en otro usuario.')