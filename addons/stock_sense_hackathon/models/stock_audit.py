# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import AccessError


class StockSenseAuditLog(models.Model):
    """Immutable business audit records for Stock Sense operations."""

    _name = 'stock.sense.audit.log'
    _description = 'Stock Sense Audit Log'
    _order = 'timestamp desc, id desc'
    _rec_name = 'record_reference'

    user_id = fields.Many2one('res.users', required=True, readonly=True,
                              default=lambda self: self.env.user)
    action = fields.Char(required=True, readonly=True, index=True)
    model_name = fields.Char(required=True, readonly=True, index=True)
    record_id = fields.Integer(required=True, readonly=True, index=True)
    record_reference = fields.Char(required=True, readonly=True)
    old_value = fields.Text(readonly=True)
    new_value = fields.Text(readonly=True)
    reason = fields.Text(readonly=True)
    timestamp = fields.Datetime(required=True, readonly=True,
                                default=fields.Datetime.now, index=True)
    details = fields.Text(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not (self.env.su or self.env.context.get('stock_sense_audit_write')):
            raise AccessError('Audit log entries can only be created by Stock Sense operations.')
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError('Audit log entries are append-only and cannot be edited.')

    def unlink(self):
        raise AccessError('Audit log entries are append-only and cannot be deleted.')

    @api.model
    def log(self, action, record, old_value='', new_value='', reason='', details=''):
        """Create an audit entry under sudo while retaining the acting user."""
        return self.sudo().with_context(stock_sense_audit_write=True).create({
            'user_id': self.env.user.id,
            'action': action,
            'model_name': record._name,
            'record_id': record.id,
            'record_reference': record.display_name or str(record.id),
            'old_value': str(old_value) if old_value is not False else '',
            'new_value': str(new_value) if new_value is not False else '',
            'reason': reason or '',
            'details': details or '',
        })
