# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import AccessError, ValidationError


class StockSenseAdjustmentRejectWizard(models.TransientModel):
    _name = 'stock.sense.adjustment.reject.wizard'
    _description = 'Reject Stock Adjustment Request'

    adjustment_id = fields.Many2one(
        'stock.sense.adjustment', required=True, readonly=True, ondelete='cascade')
    rejection_reason = fields.Text(required=True)

    def _require_manager(self):
        if not self.env.user.has_group('stock_sense_hackathon.group_stock_sense_manager'):
            raise AccessError(_('Only StockSense Managers can reject adjustments.'))

    def action_confirm_rejection(self):
        self.ensure_one()
        self._require_manager()
        reason = (self.rejection_reason or '').strip()
        if not reason:
            raise ValidationError(_('Provide a rejection reason before rejecting this request.'))
        self.adjustment_id.action_reject(reason)
        return {'type': 'ir.actions.act_window_close'}
