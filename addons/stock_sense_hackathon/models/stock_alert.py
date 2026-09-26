# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockSenseAlert(models.Model):
    """
    Stock Sense Alert system.
    Tracks low-stock, overstock, expiry, and IoT-triggered alerts.
    """
    _name = 'stock.sense.alert'
    _description = 'Stock Sense – Stock Alert'
    _order = 'priority desc, create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    # ─── Identification ────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Alert',
        compute='_compute_display_name',
        store=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Warehouse Location',
        domain=[('usage', '=', 'internal')],
    )

    # ─── Alert Type & Priority ─────────────────────────────────────────────
    alert_type = fields.Selection(
        selection=[
            ('low_stock', '⚠️ Low Stock'),
            ('stockout', '🚨 Stockout'),
            ('overstock', '📦 Overstock'),
            ('expiry', '⏰ Near Expiry'),
            ('demand_spike', '📈 Demand Spike'),
            ('iot_anomaly', '🔌 IoT Anomaly'),
            ('replenishment', '🔄 Replenishment Due'),
        ],
        string='Alert Type',
        required=True,
        tracking=True,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', '⭐ Important'),
            ('2', '⭐⭐ Urgent'),
            ('3', '⭐⭐⭐ Critical'),
        ],
        string='Priority',
        default='0',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('open', '🔴 Open'),
            ('in_progress', '🟡 In Progress'),
            ('escalated', '🚨 Escalated'),
            ('resolved', '✅ Resolved'),
            ('dismissed', '❌ Dismissed'),
        ],
        string='Status',
        default='open',
        required=True,
        tracking=True,
    )

    # ─── Alert Details ─────────────────────────────────────────────────────
    current_qty = fields.Float(
        string='Current Stock Level',
        digits='Product Unit of Measure',
        default=0.0,
    )
    threshold_qty = fields.Float(
        string='Threshold',
        digits='Product Unit of Measure',
        default=0.0,
        help='The threshold that triggered this alert',
    )
    recommended_action = fields.Text(
        string='Recommended Action',
        help='AI-suggested action to resolve this alert',
    )
    source = fields.Selection(
        selection=[
            ('system', '🤖 System / Scheduled'),
            ('iot', '📡 IoT Sensor'),
            ('manual', '👤 Manual'),
            ('forecast', '🧠 AI Forecast'),
        ],
        string='Alert Source',
        default='system',
    )
    trigger_date = fields.Datetime(
        string='Triggered On',
        default=fields.Datetime.now,
        required=True,
    )
    resolved_date = fields.Datetime(
        string='Resolved On',
        readonly=True,
    )
    resolved_by = fields.Many2one(
        comodel_name='res.users',
        string='Resolved By',
        readonly=True,
    )
    notes = fields.Text(string='Resolution Notes')

    # ─── Replenishment Link ────────────────────────────────────────────────
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Linked PO',
        help='Purchase order created to resolve this alert',
    )
    iot_sensor_id = fields.Many2one(
        comodel_name='stock.sense.iot.sensor',
        string='IoT Sensor',
        help='Sensor that triggered this alert',
    )

    # ─── Compute ───────────────────────────────────────────────────────────

    @api.depends('product_tmpl_id', 'alert_type', 'trigger_date')
    def _compute_display_name(self):
        type_labels = dict(self._fields['alert_type'].selection)
        for rec in self:
            product = rec.product_tmpl_id.name or 'Unknown'
            atype = type_labels.get(rec.alert_type, '')
            date = rec.trigger_date.strftime('%Y-%m-%d %H:%M') if rec.trigger_date else ''
            rec.display_name = f"{atype} – {product} ({date})"

    # ─── Automation ────────────────────────────────────────────────────────

    @api.model
    def _cron_check_stock_levels(self):
        """
        Scheduled action: check all Stock Sense-enabled products and
        auto-generate alerts when thresholds are breached.
        """
        products = self.env['product.template'].search([
            ('stock_sense_enabled', '=', True),
        ])
        _logger.info("Stock Sense cron: checking %d products", len(products))

        for product in products:
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
            ])
            current_qty = sum(quants.mapped('quantity'))

            # ── Low Stock / Stockout ──
            if current_qty <= 0:
                self._create_alert_if_missing(product, 'stockout', current_qty,
                                              product.alert_low_stock_threshold, '3')
            elif current_qty < product.alert_low_stock_threshold:
                self._create_alert_if_missing(product, 'low_stock', current_qty,
                                              product.alert_low_stock_threshold, '2')

            # ── Overstock ──
            elif current_qty > product.alert_overstock_threshold:
                self._create_alert_if_missing(product, 'overstock', current_qty,
                                              product.alert_overstock_threshold, '1')

            # ── Resolve stale alerts if stock is healthy ──
            else:
                stale_alerts = self.search([
                    ('product_tmpl_id', '=', product.id),
                    ('alert_type', 'in', ['low_stock', 'stockout', 'overstock']),
                    ('state', '=', 'open'),
                ])
                stale_alerts._auto_resolve("Stock level returned to normal range.")

    def _create_alert_if_missing(self, product, alert_type, current_qty, threshold, priority):
        """Only create a new alert if no open alert of same type exists."""
        existing = self.search([
            ('product_tmpl_id', '=', product.id),
            ('alert_type', '=', alert_type),
            ('state', '=', 'open'),
        ], limit=1)
        if not existing:
            action_map = {
                'stockout': f'Product is OUT OF STOCK. Immediately create a purchase order for at least {product.sense_recommended_qty:.0f} units.',
                'low_stock': f'Stock is below threshold ({threshold} units). Consider ordering {product.sense_recommended_qty:.0f} units.',
                'overstock': f'Excess inventory detected. Consider promotions or returning {current_qty - threshold:.0f} units.',
            }
            self.create({
                'product_tmpl_id': product.id,
                'alert_type': alert_type,
                'priority': priority,
                'current_qty': current_qty,
                'threshold_qty': threshold,
                'source': 'system',
                'recommended_action': action_map.get(alert_type, ''),
            })
            _logger.info("Alert created: %s for %s (qty=%.2f)", alert_type, product.name, current_qty)

    def _auto_resolve(self, message):
        for rec in self:
            rec.write({
                'state': 'resolved',
                'resolved_date': fields.Datetime.now(),
                'resolved_by': self.env.user.id,
                'notes': message,
            })

    # ─── Manual Actions ─────────────────────────────────────────────────────

    def action_resolve(self):
        self._auto_resolve("Manually resolved by user.")
        return True

    def action_escalate(self):
        self.write({'state': 'escalated', 'priority': '3'})
        self.message_post(body="🚨 Alert escalated to critical priority.")

    def action_dismiss(self):
        self.write({'state': 'dismissed'})

    def action_create_po(self):
        """Auto-create a purchase order from the alert."""
        self.ensure_one()
        product = self.product_tmpl_id
        if not product.seller_ids:
            raise ValidationError(
                f"No vendor configured for {product.name}. Please add a vendor first."
            )
        vendor = product.seller_ids[0].partner_id
        po = self.env['purchase.order'].create({
            'partner_id': vendor.id,
            'order_line': [(0, 0, {
                'product_id': product.product_variant_ids[0].id,
                'product_qty': product.sense_recommended_qty or self.threshold_qty,
                'price_unit': product.seller_ids[0].price,
                'date_planned': fields.Datetime.now(),
            })],
        })
        self.write({
            'purchase_order_id': po.id,
            'state': 'in_progress',
        })
        self.message_post(body=f"✅ Purchase Order {po.name} created automatically by Stock Sense.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
        }
