# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockSenseIotSensor(models.Model):
    """
    IoT Sensor registry for Stock Sense.
    Manages Raspberry Pi weight/RFID sensors and their real-time readings.
    """
    _name = 'stock.sense.iot.sensor'
    _description = 'Stock Sense – IoT Sensor'
    _order = 'name asc'
    _inherit = ['mail.thread']

    # ─── Identification ────────────────────────────────────────────────────
    name = fields.Char(string='Sensor Name', required=True, tracking=True)
    sensor_uid = fields.Char(
        string='Sensor UID',
        required=True,
        copy=False,
        help='Unique hardware identifier (e.g. Raspberry Pi serial number)',
    )
    sensor_type = fields.Selection(
        selection=[
            ('weight', '⚖️ Weight Scale'),
            ('rfid', '📡 RFID Reader'),
            ('barcode', '🔍 Barcode Scanner'),
            ('temperature', '🌡️ Temperature Sensor'),
            ('humidity', '💧 Humidity Sensor'),
            ('proximity', '📏 Proximity Sensor'),
        ],
        string='Sensor Type',
        required=True,
        default='weight',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('offline', '⚫ Offline'),
            ('online', '🟢 Online'),
            ('error', '🔴 Error'),
            ('maintenance', '🟡 Maintenance'),
        ],
        string='Status',
        default='offline',
        tracking=True,
    )

    # ─── Product & Location ────────────────────────────────────────────────
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Monitored Product',
        index=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Warehouse Location',
        domain=[('usage', '=', 'internal')],
    )

    # ─── Connection ────────────────────────────────────────────────────────
    ip_address = fields.Char(
        string='IP Address / Hostname',
        help='IP or hostname of the Raspberry Pi',
    )
    port = fields.Integer(
        string='Port',
        default=8080,
        help='API port exposed by the Raspberry Pi',
    )
    api_endpoint = fields.Char(
        string='Endpoint URL',
        compute='_compute_api_endpoint',
        store=True,
    )
    api_token = fields.Char(
        string='API Token',
        help='Authentication token for the IoT device API',
        groups='stock.group_stock_manager',
    )
    polling_interval = fields.Integer(
        string='Polling Interval (seconds)',
        default=60,
        help='How often to read sensor data (minimum 10 seconds)',
    )

    # ─── Readings ─────────────────────────────────────────────────────────
    last_reading_value = fields.Float(
        string='Last Reading',
        readonly=True,
        digits=(16, 4),
    )
    last_reading_unit = fields.Char(
        string='Unit',
        readonly=True,
        default='kg',
    )
    last_reading_date = fields.Datetime(
        string='Last Reading Date',
        readonly=True,
    )
    reading_count = fields.Integer(
        string='Total Readings',
        compute='_compute_reading_count',
    )

    # ─── Calibration ──────────────────────────────────────────────────────
    calibration_factor = fields.Float(
        string='Calibration Factor',
        default=1.0,
        help='Multiply raw sensor value by this factor to get real unit value',
    )
    tare_weight = fields.Float(
        string='Tare Weight (kg)',
        default=0.0,
        help='Empty container weight to subtract from readings',
    )
    unit_weight = fields.Float(
        string='Unit Weight (kg)',
        default=0.0,
        help='Weight of one product unit (for qty calculation)',
    )

    # ─── Thresholds ───────────────────────────────────────────────────────
    min_threshold = fields.Float(
        string='Min Alert Threshold',
        default=5.0,
    )
    max_threshold = fields.Float(
        string='Max Alert Threshold',
        default=200.0,
    )
    alert_on_anomaly = fields.Boolean(
        string='Alert on Anomaly',
        default=True,
        help='Raise alert if reading deviates significantly from expected value',
    )

    # ─── Reading History ───────────────────────────────────────────────────
    reading_ids = fields.One2many(
        comodel_name='stock.sense.iot.reading',
        inverse_name='sensor_id',
        string='Reading History',
    )

    # ─── Compute ───────────────────────────────────────────────────────────

    @api.depends('ip_address', 'port')
    def _compute_api_endpoint(self):
        for rec in self:
            if rec.ip_address and rec.port:
                rec.api_endpoint = f"http://{rec.ip_address}:{rec.port}/api/v1/reading"
            else:
                rec.api_endpoint = ''

    def _compute_reading_count(self):
        for rec in self:
            rec.reading_count = self.env['stock.sense.iot.reading'].search_count([
                ('sensor_id', '=', rec.id),
            ])

    # ─── IoT Actions ───────────────────────────────────────────────────────

    def action_poll_sensor(self):
        """Manually poll a single sensor for latest reading."""
        self.ensure_one()
        reading = self._fetch_reading()
        if reading is not None:
            self._process_reading(reading)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Sensor Polled',
                    'message': f"Reading: {reading} {self.last_reading_unit}",
                    'type': 'success',
                },
            }

    def _fetch_reading(self):
        """
        Fetch real-time reading from IoT device via HTTP.
        Returns float value or None on failure.
        """
        import requests
        if not self.api_endpoint:
            _logger.warning("Sensor %s has no API endpoint configured", self.name)
            return None
        try:
            headers = {}
            if self.api_token:
                headers['Authorization'] = f"Bearer {self.api_token}"
            response = requests.get(self.api_endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            raw_value = data.get('value', data.get('reading', 0))
            # Apply calibration
            calibrated = (float(raw_value) - self.tare_weight) * self.calibration_factor
            return max(0.0, calibrated)
        except Exception as e:
            _logger.error("Failed to poll sensor %s: %s", self.name, str(e))
            self.state = 'error'
            return None

    def _process_reading(self, value):
        """Store reading, update product qty, and check thresholds."""
        self.ensure_one()
        now = fields.Datetime.now()

        # Store reading record
        self.env['stock.sense.iot.reading'].create({
            'sensor_id': self.id,
            'reading_date': now,
            'raw_value': value,
            'unit': self.last_reading_unit,
        })

        # Update sensor state
        self.write({
            'last_reading_value': value,
            'last_reading_date': now,
            'state': 'online',
        })

        # Update product IoT reading
        if self.product_tmpl_id:
            self.product_tmpl_id.write({
                'iot_current_weight': value,
                'iot_last_reading': now,
            })

        # Check thresholds and raise alert if needed
        if self.alert_on_anomaly:
            if value < self.min_threshold:
                self.env['stock.sense.alert'].create({
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'iot_sensor_id': self.id,
                    'alert_type': 'iot_anomaly',
                    'priority': '2',
                    'current_qty': value,
                    'threshold_qty': self.min_threshold,
                    'source': 'iot',
                    'recommended_action': f"Sensor {self.name} reading below minimum ({value:.2f} < {self.min_threshold:.2f}). Verify stock and sensor calibration.",
                })

    @api.model
    def _cron_poll_all_sensors(self):
        """Scheduled action: poll all online/offline sensors."""
        sensors = self.search([('state', 'in', ['online', 'offline'])])
        _logger.info("IoT cron: polling %d sensors", len(sensors))
        for sensor in sensors:
            reading = sensor._fetch_reading()
            if reading is not None:
                sensor._process_reading(reading)

    @api.constrains('polling_interval')
    def _check_polling_interval(self):
        for rec in self:
            if rec.polling_interval < 10:
                raise ValidationError("Polling interval must be at least 10 seconds.")


class StockSenseIotReading(models.Model):
    """Historical IoT sensor readings log."""
    _name = 'stock.sense.iot.reading'
    _description = 'Stock Sense – IoT Reading Log'
    _order = 'reading_date desc'

    sensor_id = fields.Many2one(
        comodel_name='stock.sense.iot.sensor',
        string='Sensor',
        required=True,
        ondelete='cascade',
        index=True,
    )
    reading_date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    raw_value = fields.Float(string='Value', digits=(16, 4))
    unit = fields.Char(string='Unit', default='kg')
    is_anomaly = fields.Boolean(string='Anomaly Detected', default=False)
    note = fields.Char(string='Note')
