from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools.mail import email_re

class BibliotecaPersonal(models.Model):
    _name = 'biblioteca.personal'
    _description = 'biblioteca.personal'
    _rec_name = 'nombre_personal'

    nombre_personal = fields.Char(string='Nombre', required=True)
    apellido_personal = fields.Char(string='Apellido', required=True)
    cedula_personal = fields.Char(string='CI o Cédula', required=True)
    personal_telefono = fields.Char(string='Celular', required=True)
    personal_direccion = fields.Char(string='Dirección', required=True)
    personal_mail = fields.Char(string='Correo electrónico', required=True)
    usuario_id = fields.Many2one('res.users', string='Usuario Odoo')

    @api.onchange('usuario_id')
    def _onchange_usuario_id(self):
        if self.usuario_id:
            partner = self.usuario_id.partner_id
            self.nombre_personal = partner.name or ""
            if partner.name and " " in partner.name:
                    partes = partner.name.split(" ", 1)
                    self.nombre_personal = partes[0]
                    self.apellido_personal = partes[1]
            else:
                self.apellido_personal = ""
            self.personal_mail = partner.email or ""
            self.personal_telefono = partner.phone or ""
            self.personal_direccion = partner.street or ""
        else:
            self.nombre_personal = ""
            self.apellido_personal = ""
            self.personal_mail = ""
            self.personal_telefono = ""
            self.personal_direccion = ""

    @api.constrains('cedula_personal')
    def _check_cedula(self):
        for record in self:
            if record.cedula_personal and not self.validar_cedula_ec(record.cedula_personal):
                raise ValidationError("Cédula ecuatoriana inválida: %s" % record.cedula_personal)

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

    @api.constrains('personal_mail')
    def _check_valid_mail(self):
        for record in self:
            if record.personal_mail and not email_re.match(record.personal_mail):
                raise ValidationError("El formato del correo electrónico no es el correcto.")
    
    @api.constrains('cedula_personal', 'personal_mail')
    def _check_unique_personal(self):
        for record in self:
            if self.search_count([('cedula_personal', '=', record.cedula_personal), ('id', '!=', record.id)]) > 0:
                raise ValidationError('La cédula ya está registrada en otro personal.')
            if self.search_count([('personal_mail', '=', record.personal_mail), ('id', '!=', record.id)]) > 0:
                raise ValidationError('El correo electrónico ya está registrado en otro personal.')