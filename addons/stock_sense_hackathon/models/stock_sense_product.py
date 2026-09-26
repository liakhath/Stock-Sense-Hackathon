# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)


class StockSenseProduct(models.Model):
    """
    Extends product.product to add Stock Sense intelligence fields.
    Tracks stock levels, demand patterns, and replenishment metrics.
    """
    _inherit = 'product.template'
    _description = 'Stock Sense Product Intelligence'

    # ─── Stock Sense Config ────────────────────────────────────────────────
    stock_sense_enabled = fields.Boolean(
        string='Enable Stock Sense',
        default=True,
        help='Enable AI-powered monitoring and forecasting for this product',
    )
    sense_reorder_point = fields.Float(
        string='Smart Reorder Point (units)',
        default=0.0,
        digits='Product Unit of Measure',
        help='AI-calculated minimum stock level before replenishment is triggered',
    )
    sense_safety_stock = fields.Float(
        string='Safety Stock (units)',
        default=0.0,
        digits='Product Unit of Measure',
        help='Buffer stock to cover demand uncertainty during lead time',
    )
    sense_lead_time = fields.Integer(
        string='Supplier Lead Time (days)',
        default=7,
        help='Average days from purchase order to stock receipt',
    )
    sense_forecast_horizon = fields.Integer(
        string='Forecast Horizon (days)',
        default=30,
        help='Number of days ahead to forecast demand',
    )

    # ─── AI Forecast Summary ───────────────────────────────────────────────
    sense_forecasted_demand = fields.Float(
        string='Forecasted Demand',
        compute='_compute_forecast_summary',
        store=True,
        digits='Product Unit of Measure',
        help='AI-predicted demand for the forecast horizon',
    )
    sense_forecast_confidence = fields.Float(
        string='Forecast Confidence (%)',
        compute='_compute_forecast_summary',
        store=True,
        help='Model confidence score (0-100)',
    )
    sense_forecast_model = fields.Selection(
        selection=[
            ('linear', 'Linear Regression'),
            ('arima', 'ARIMA'),
            ('random_forest', 'Random Forest'),
            ('auto', 'Auto (Best Fit)'),
        ],
        string='Forecast Algorithm',
        default='auto',
    )
    sense_last_forecast_date = fields.Datetime(
        string='Last Forecast Run',
        readonly=True,
    )

    # ─── IoT Sensor ────────────────────────────────────────────────────────
    iot_sensor_ids = fields.One2many(
        comodel_name='stock.sense.iot.sensor',
        inverse_name='product_tmpl_id',
        string='IoT Sensors',
    )
    iot_sensor_count = fields.Integer(
        string='Sensor Count',
        compute='_compute_iot_sensor_count',
    )
    iot_current_weight = fields.Float(
        string='Current Sensor Reading (kg)',
        readonly=True,
        help='Latest weight reading from IoT sensor',
    )
    iot_last_reading = fields.Datetime(
        string='Last IoT Reading',
        readonly=True,
    )

    # ─── Alert Thresholds ──────────────────────────────────────────────────
    alert_low_stock_threshold = fields.Float(
        string='Low Stock Alert Threshold',
        default=10.0,
        help='Send alert when stock falls below this level',
    )
    alert_overstock_threshold = fields.Float(
        string='Overstock Alert Threshold',
        default=500.0,
        help='Send alert when stock exceeds this level',
    )
    alert_expiry_days = fields.Integer(
        string='Expiry Alert (days before)',
        default=30,
        help='Alert X days before product expiry',
    )

    # ─── Replenishment Stats ───────────────────────────────────────────────
    sense_avg_daily_demand = fields.Float(
        string='Avg Daily Demand',
        compute='_compute_demand_stats',
        store=True,
        digits='Product Unit of Measure',
    )
    sense_stockout_risk = fields.Selection(
        selection=[
            ('low', '🟢 Low'),
            ('medium', '🟡 Medium'),
            ('high', '🔴 High'),
            ('critical', '🚨 Critical'),
        ],
        string='Stockout Risk',
        compute='_compute_stockout_risk',
        store=True,
    )
    sense_recommended_qty = fields.Float(
        string='Recommended Order Qty',
        compute='_compute_recommended_qty',
        store=True,
        digits='Product Unit of Measure',
    )

    # ─── Alert Relation ────────────────────────────────────────────────────
    stock_alert_ids = fields.One2many(
        comodel_name='stock.sense.alert',
        inverse_name='product_tmpl_id',
        string='Stock Alerts',
    )
    active_alert_count = fields.Integer(
        string='Active Alerts',
        compute='_compute_active_alert_count',
    )
    forecast_ids = fields.One2many(
        comodel_name='stock.sense.forecast',
        inverse_name='product_tmpl_id',
        string='Forecasts',
    )

    # ─── Compute Methods ───────────────────────────────────────────────────

    def _compute_iot_sensor_count(self):
        for rec in self:
            rec.iot_sensor_count = len(rec.iot_sensor_ids)

    def _compute_active_alert_count(self):
        for rec in self:
            rec.active_alert_count = self.env['stock.sense.alert'].search_count([
                ('product_tmpl_id', '=', rec.id),
                ('state', 'in', ['open', 'escalated']),
            ])

    @api.depends('forecast_ids.forecasted_qty', 'forecast_ids.confidence_score', 'forecast_ids.state')
    def _compute_forecast_summary(self):
        for rec in self:
            latest = self.env['stock.sense.forecast'].search([
                ('product_tmpl_id', '=', rec.id),
                ('state', '=', 'done'),
            ], order='forecast_date desc', limit=1)
            if latest:
                rec.sense_forecasted_demand = latest.forecasted_qty
                rec.sense_forecast_confidence = latest.confidence_score
                rec.sense_last_forecast_date = latest.forecast_date
            else:
                rec.sense_forecasted_demand = 0.0
                rec.sense_forecast_confidence = 0.0
                rec.sense_last_forecast_date = False

    @api.depends('forecast_ids')
    def _compute_demand_stats(self):
        for rec in self:
            forecasts = self.env['stock.sense.forecast'].search([
                ('product_tmpl_id', '=', rec.id),
                ('state', '=', 'done'),
            ], limit=10, order='forecast_date desc')
            if forecasts and rec.sense_forecast_horizon:
                total = sum(f.forecasted_qty for f in forecasts)
                days = rec.sense_forecast_horizon * len(forecasts)
                rec.sense_avg_daily_demand = total / days if days else 0.0
            else:
                rec.sense_avg_daily_demand = 0.0

    @api.depends('sense_avg_daily_demand', 'sense_lead_time', 'sense_safety_stock')
    def _compute_stockout_risk(self):
        for rec in self:
            # Get current qty on hand across all locations
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', rec.id),
                ('location_id.usage', '=', 'internal'),
            ])
            current_qty = sum(quants.mapped('quantity'))
            demand_during_lead = rec.sense_avg_daily_demand * rec.sense_lead_time

            if current_qty <= 0:
                rec.sense_stockout_risk = 'critical'
            elif current_qty < demand_during_lead:
                rec.sense_stockout_risk = 'high'
            elif current_qty < demand_during_lead + rec.sense_safety_stock:
                rec.sense_stockout_risk = 'medium'
            else:
                rec.sense_stockout_risk = 'low'

    @api.depends('sense_avg_daily_demand', 'sense_lead_time', 'sense_safety_stock', 'sense_forecast_horizon')
    def _compute_recommended_qty(self):
        for rec in self:
            # Economic Order Quantity approximation:
            # Recommended Qty = (Avg daily demand × forecast horizon) + safety_stock
            rec.sense_recommended_qty = (
                rec.sense_avg_daily_demand * rec.sense_forecast_horizon
                + rec.sense_safety_stock
            )

    # ─── Actions ────────────────────────────────────────────────────────────

    def action_run_forecast(self):
        """Open the existing forecast form for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Run AI Forecast'),
            'res_model': 'stock.sense.forecast',
            'view_mode': 'form',
            'view_id': self.env.ref('stock_sense_hackathon.view_stock_sense_forecast_form').id,
            'target': 'current',
            'context': {
                'default_product_tmpl_id': self.id,
                'default_algorithm': self.sense_forecast_model,
            },
        }

    def action_view_alerts(self):
        """Open alerts for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Alerts',
            'res_model': 'stock.sense.alert',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_view_sensors(self):
        """Open IoT sensors for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'IoT Sensors',
            'res_model': 'stock.sense.iot.sensor',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_smart_replenish(self):
        """Open existing reorder suggestions for this product."""
        self.ensure_one()
        if not self.env.user.has_group('stock_sense_hackathon.group_stock_sense_manager'):
            raise AccessError(_('Only StockSense Managers can view smart replenishment suggestions.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Smart Replenishment'),
            'res_model': 'stock.sense.reorder.suggestion',
            'view_mode': 'tree,form',
            'view_id': self.env.ref('stock_sense_hackathon.view_stock_sense_reorder_list').id,
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'target': 'current',
        }

    @api.constrains('alert_low_stock_threshold', 'alert_overstock_threshold')
    def _check_thresholds(self):
        for rec in self:
            if rec.alert_low_stock_threshold >= rec.alert_overstock_threshold:
                raise ValidationError(
                    "Low stock threshold must be less than overstock threshold."
                )
