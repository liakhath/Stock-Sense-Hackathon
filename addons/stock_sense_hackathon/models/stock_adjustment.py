# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockSenseAdjustment(models.Model):
    _name = 'stock.sense.adjustment'
    _description = 'Stock Sense Stock Adjustment Request'
    _order = 'requested_at desc, id desc'
    _rec_name = 'name'

    name = fields.Char(default=lambda self: _('New'), readonly=True, copy=False)
    product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    warehouse_id = fields.Many2one('stock.warehouse', required=True, ondelete='restrict',
                                   default=lambda self: self.env['stock.warehouse'].search([], limit=1))
    current_quantity = fields.Float(required=True, readonly=True, digits='Product Unit of Measure')
    requested_quantity = fields.Float(required=True, digits='Product Unit of Measure')
    quantity_difference = fields.Float(compute='_compute_quantity_difference', store=True,
                                       digits='Product Unit of Measure')
    reason = fields.Char(required=True)
    comment = fields.Text()
    requested_by = fields.Many2one('res.users', required=True, readonly=True,
                                   default=lambda self: self.env.user, index=True)
    requested_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    approved_by = fields.Many2one('res.users', readonly=True)
    approved_at = fields.Datetime(readonly=True)
    rejected_by = fields.Many2one('res.users', readonly=True)
    rejected_at = fields.Datetime(readonly=True)
    rejection_reason = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'),
        ('rejected', 'Rejected'), ('cancelled', 'Cancelled'),
    ], default='draft', required=True, readonly=True, index=True)

    @api.depends('requested_quantity', 'current_quantity')
    def _compute_quantity_difference(self):
        for record in self:
            record.quantity_difference = record.requested_quantity - record.current_quantity

    @api.constrains('requested_quantity')
    def _check_requested_quantity(self):
        for record in self:
            if record.requested_quantity < 0:
                raise ValidationError(_('Requested quantity cannot be negative.'))

    @api.model
    def _quantity_at_warehouse(self, product, warehouse):
        if not product or not warehouse:
            return 0.0
        quants = self.env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('location_id', 'child_of', warehouse.view_location_id.id),
            ('location_id.usage', '=', 'internal'),
        ])
        return sum(quants.mapped('quantity'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('warehouse_id'):
                default_warehouse = self.env['stock.warehouse'].search([], limit=1)
                vals['warehouse_id'] = default_warehouse.id
            warehouse = self.env['stock.warehouse'].browse(vals.get('warehouse_id'))
            product = self.env['product.product'].browse(vals.get('product_id'))
            if not warehouse or not product:
                raise ValidationError(_('A product and warehouse are required.'))
            vals.setdefault('current_quantity', self._quantity_at_warehouse(product, warehouse))
            vals.setdefault('requested_by', self.env.user.id)
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.sense.adjustment') or _('New')
        records = super().create(vals_list)
        for record in records:
            self.env['stock.sense.audit.log'].log(
                'STOCK_ADJUSTMENT_CREATED', record, record.current_quantity,
                record.requested_quantity, record.reason)
        return records

    def write(self, vals):
        if not self.env.context.get('stock_sense_adjustment_transition'):
            for record in self:
                if record.state != 'draft':
                    raise UserError(_('Only draft adjustment requests can be edited.'))
                if record.requested_by != self.env.user and not self.env.user.has_group(
                        'stock_sense_hackathon.group_stock_sense_manager'):
                    raise AccessError(_('You can only edit your own adjustment requests.'))
                if 'state' in vals:
                    raise AccessError(_('Use the adjustment workflow actions to change state.'))
        return super().write(vals)

    def action_submit(self):
        for record in self:
            if record.state != 'draft' or record.requested_by != self.env.user:
                raise AccessError(_('Only the requester can submit a draft adjustment.'))
            record.with_context(stock_sense_adjustment_transition=True).write({'state': 'pending'})
            self.env['stock.sense.audit.log'].log(
                'STOCK_ADJUSTMENT_SUBMITTED', record, record.current_quantity,
                record.requested_quantity, record.reason)
        return True

    def _check_manager_approval(self):
        if not self.env.user.has_group('stock_sense_hackathon.group_stock_sense_manager'):
            raise AccessError(_('Only StockSense Managers can approve or reject adjustments.'))
        for record in self:
            if record.requested_by == self.env.user:
                raise AccessError(_('You cannot approve or reject your own adjustment request.'))
            if record.state != 'pending':
                raise UserError(_('Only pending adjustment requests can be processed.'))

    def action_approve(self):
        self._check_manager_approval()
        for record in self:
            actual_quantity = self._quantity_at_warehouse(record.product_id, record.warehouse_id)
            if record.requested_quantity < 0:
                raise ValidationError(_('Insufficient stock. Available quantity is %s.') % actual_quantity)
            difference = record.requested_quantity - actual_quantity
            if difference < 0 and actual_quantity + difference < 0:
                raise ValidationError(_('Insufficient stock. Available quantity is %s.') % actual_quantity)
            if difference:
                self.env['stock.quant'].sudo()._update_available_quantity(
                    record.product_id, record.warehouse_id.lot_stock_id, difference)
            record.with_context(stock_sense_adjustment_transition=True).write({
                'current_quantity': actual_quantity,
                'state': 'approved', 'approved_by': self.env.user.id,
                'approved_at': fields.Datetime.now(),
            })
            self.env['stock.sense.audit.log'].log(
                'STOCK_ADJUSTMENT_APPROVED', record, actual_quantity,
                record.requested_quantity, record.reason)
            self.env['stock.sense.audit.log'].log(
                'STOCK_UPDATED', record, actual_quantity,
                record.requested_quantity, record.reason,
                _('Applied through approved adjustment %s.') % record.name)
        return True

    def action_reject(self):
        self._check_manager_approval()
        for record in self:
            if not record.rejection_reason:
                raise ValidationError(_('Provide a rejection reason before rejecting this request.'))
            record.with_context(stock_sense_adjustment_transition=True).write({
                'state': 'rejected', 'rejected_by': self.env.user.id,
                'rejected_at': fields.Datetime.now(),
            })
            self.env['stock.sense.audit.log'].log(
                'STOCK_ADJUSTMENT_REJECTED', record, record.current_quantity,
                record.requested_quantity, record.rejection_reason)
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ('draft', 'pending') or record.requested_by != self.env.user:
                raise AccessError(_('Only the requester can cancel a draft or pending request.'))
            record.with_context(stock_sense_adjustment_transition=True).write({'state': 'cancelled'})
        return True
