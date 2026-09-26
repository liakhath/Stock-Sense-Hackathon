# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockSenseReorderSuggestion(models.Model):
    _name = 'stock.sense.reorder.suggestion'
    _description = 'Stock Sense Reorder Suggestion'
    _order = 'generated_at desc, id desc'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', required=True, ondelete='cascade')
    warehouse_id = fields.Many2one('stock.warehouse', required=True, ondelete='cascade')
    current_stock = fields.Float(readonly=True, digits='Product Unit of Measure')
    minimum_stock = fields.Float(readonly=True, digits='Product Unit of Measure')
    average_daily_usage = fields.Float(readonly=True, digits='Product Unit of Measure')
    lead_time_days = fields.Integer(readonly=True)
    safety_stock = fields.Float(readonly=True, digits='Product Unit of Measure')
    reorder_point = fields.Float(readonly=True, digits='Product Unit of Measure')
    suggested_quantity = fields.Float(readonly=True, digits='Product Unit of Measure')
    days_until_stockout = fields.Float(readonly=True, digits=(16, 2))
    reason = fields.Text(readonly=True)
    generated_at = fields.Datetime(default=fields.Datetime.now, readonly=True)
    state = fields.Selection([('required', 'Reorder Required'), ('resolved', 'Resolved')],
                             default='required', readonly=True)

    @api.model
    def generate_suggestions(self):
        """Generate current low-stock suggestions using product forecast metrics."""
        Adjustment = self.env['stock.sense.adjustment']
        products = self.env['product.product'].search([
            ('product_tmpl_id.stock_sense_enabled', '=', True), ('active', '=', True),
        ])
        warehouses = self.env['stock.warehouse'].search([])
        created = self.browse()
        for product in products:
            template = product.product_tmpl_id
            usage = template.sense_avg_daily_demand or 0.0
            reorder_point = usage * template.sense_lead_time + template.sense_safety_stock
            for warehouse in warehouses:
                current = Adjustment._quantity_at_warehouse(product, warehouse)
                if current <= reorder_point:
                    existing = self.search([
                        ('product_id', '=', product.id), ('warehouse_id', '=', warehouse.id),
                        ('state', '=', 'required'),
                    ], limit=1)
                    vals = {
                        'current_stock': current,
                        'minimum_stock': template.alert_low_stock_threshold,
                        'average_daily_usage': usage,
                        'lead_time_days': template.sense_lead_time,
                        'safety_stock': template.sense_safety_stock,
                        'reorder_point': reorder_point,
                        'suggested_quantity': max(reorder_point - current, template.sense_recommended_qty),
                        'days_until_stockout': current / usage if usage else 0.0,
                        'reason': _('Current stock %(stock)s is at or below reorder point %(point)s (usage %(usage)s/day, lead time %(lead)s days, safety stock %(safety)s).') % {
                            'stock': current, 'point': reorder_point, 'usage': usage,
                            'lead': template.sense_lead_time, 'safety': template.sense_safety_stock,
                        },
                    }
                    if existing:
                        existing.write(vals)
                        suggestion = existing
                    else:
                        vals.update({'product_id': product.id, 'warehouse_id': warehouse.id})
                        suggestion = self.create(vals)
                        self.env['stock.sense.audit.log'].log(
                            'REORDER_SUGGESTED', suggestion, '', suggestion.suggested_quantity,
                            suggestion.reason)
                    created |= suggestion
        return created

    def action_mark_resolved(self):
        self.write({'state': 'resolved'})

    def action_generate_suggestions(self):
        self.generate_suggestions()
        return True
