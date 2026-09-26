# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockSenseForecast(models.Model):
    """
    AI-powered demand forecast records for each product.
    Stores historical forecasts and model results from Scikit-learn / ARIMA.
    """
    _name = 'stock.sense.forecast'
    _description = 'Stock Sense – AI Demand Forecast'
    _order = 'forecast_date desc'
    _rec_name = 'display_name'

    # ─── Core Fields ───────────────────────────────────────────────────────
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
    )
    forecast_date = fields.Datetime(
        string='Forecast Run Date',
        default=fields.Datetime.now,
        required=True,
    )
    forecast_start = fields.Date(
        string='Period Start',
        required=True,
        default=fields.Date.today,
    )
    forecast_end = fields.Date(
        string='Period End',
        required=True,
        default=lambda self: (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
    )
    horizon_days = fields.Integer(
        string='Horizon (days)',
        compute='_compute_horizon_days',
        store=True,
    )

    # ─── Model & Results ───────────────────────────────────────────────────
    algorithm = fields.Selection(
        selection=[
            ('linear', 'Linear Regression'),
            ('arima', 'ARIMA'),
            ('random_forest', 'Random Forest'),
            ('gradient_boost', 'Gradient Boosting'),
            ('auto', 'Auto (Best Fit)'),
        ],
        string='Algorithm Used',
        default='auto',
        required=True,
    )
    forecasted_qty = fields.Float(
        string='Forecasted Demand (units)',
        digits='Product Unit of Measure',
        default=0.0,
    )
    forecasted_qty_min = fields.Float(
        string='Lower Bound',
        digits='Product Unit of Measure',
        default=0.0,
        help='Lower confidence interval',
    )
    forecasted_qty_max = fields.Float(
        string='Upper Bound',
        digits='Product Unit of Measure',
        default=0.0,
        help='Upper confidence interval',
    )
    confidence_score = fields.Float(
        string='Confidence Score (%)',
        default=0.0,
        help='Model accuracy confidence from 0-100',
    )
    mae = fields.Float(
        string='MAE (Mean Absolute Error)',
        default=0.0,
        help='Mean Absolute Error of the forecast model',
    )
    rmse = fields.Float(
        string='RMSE',
        default=0.0,
        help='Root Mean Square Error',
    )
    r2_score = fields.Float(
        string='R² Score',
        default=0.0,
        help='Coefficient of determination (goodness of fit)',
    )
    training_data_points = fields.Integer(
        string='Training Data Points',
        default=0,
        help='Number of historical sales records used for training',
    )

    # ─── Status ────────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('running', '⏳ Running'),
            ('done', '✅ Completed'),
            ('failed', '❌ Failed'),
        ],
        string='Status',
        default='draft',
        required=True,
    )
    error_message = fields.Text(
        string='Error Details',
        readonly=True,
    )
    notes = fields.Text(string='Notes')

    # ─── Computed ──────────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )
    daily_forecast_line_ids = fields.One2many(
        comodel_name='stock.sense.forecast.line',
        inverse_name='forecast_id',
        string='Daily Forecast Breakdown',
    )

    # ─── Compute Methods ───────────────────────────────────────────────────

    @api.depends('forecast_start', 'forecast_end')
    def _compute_horizon_days(self):
        for rec in self:
            if rec.forecast_start and rec.forecast_end:
                delta = rec.forecast_end - rec.forecast_start
                rec.horizon_days = delta.days
            else:
                rec.horizon_days = 0

    @api.depends('product_tmpl_id', 'forecast_date', 'algorithm')
    def _compute_display_name(self):
        for rec in self:
            product = rec.product_tmpl_id.name or 'Unknown'
            date = rec.forecast_date.strftime('%Y-%m-%d') if rec.forecast_date else ''
            algo = dict(rec._fields['algorithm'].selection).get(rec.algorithm, '')
            rec.display_name = f"[{algo}] {product} – {date}"

    # ─── Actions ────────────────────────────────────────────────────────────

    def action_run(self):
        """
        Trigger the AI forecast engine.
        Calls the Python ML service to train and predict.
        """
        for rec in self:
            rec.state = 'running'
            try:
                rec._execute_forecast()
                rec.state = 'done'
                rec.forecast_date = fields.Datetime.now()
            except Exception as e:
                _logger.error("Forecast failed for %s: %s", rec.product_tmpl_id.name, str(e))
                rec.state = 'failed'
                rec.error_message = str(e)

    def _execute_forecast(self):
        """
        Core ML forecast logic using Scikit-learn.
        Collects historical sales data and runs selected algorithm.
        """
        self.ensure_one()
        try:
            import numpy as np
            import pandas as pd
            from sklearn.linear_model import LinearRegression
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            from sklearn.model_selection import train_test_split
        except ImportError as e:
            raise UserError(
                f"ML libraries not installed. Run: pip install -r requirements.txt\n\nError: {e}"
            )

        # ── 1. Collect historical sales/moves ──────────────────────────────
        domain = [
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('state', '=', 'done'),
            ('date', '>=', fields.Date.today() - timedelta(days=365)),
        ]
        moves = self.env['stock.move'].search(domain + [
            ('location_dest_id.usage', '=', 'customer'),
        ])

        if not moves:
            _logger.warning("No historical sales data for %s", self.product_tmpl_id.name)
            self.forecasted_qty = self.product_tmpl_id.sense_avg_daily_demand * self.horizon_days
            self.confidence_score = 0.0
            self.training_data_points = 0
            return

        # ── 2. Build time-series DataFrame ────────────────────────────────
        records = []
        for move in moves:
            records.append({
                'date': move.date.date(),
                'qty': move.product_uom_qty,
            })

        df = pd.DataFrame(records)
        df = df.groupby('date')['qty'].sum().reset_index()
        df = df.sort_values('date')

        # Fill missing dates with 0
        date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.columns = ['date', 'qty']

        self.training_data_points = len(df)

        if len(df) < 5:
            # Not enough data – use simple average
            self.forecasted_qty = df['qty'].mean() * self.horizon_days
            self.confidence_score = 20.0
            return

        # ── 3. Feature Engineering ────────────────────────────────────────
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['day_of_month'] = pd.to_datetime(df['date']).dt.day
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['trend'] = range(len(df))

        feature_cols = ['day_of_week', 'day_of_month', 'month', 'trend']
        X = df[feature_cols].values
        y = df['qty'].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # ── 4. Select and Train Model ──────────────────────────────────────
        algorithm = self.algorithm
        models_map = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
        }

        if algorithm == 'auto' or algorithm not in models_map:
            # Try all models and pick best R² on test set
            best_model = None
            best_r2 = -float('inf')
            for name, model in models_map.items():
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                r2 = r2_score(y_test, pred)
                if r2 > best_r2:
                    best_r2 = r2
                    best_model = model
                    self.algorithm = name
            clf = best_model
        else:
            clf = models_map[algorithm]
            clf.fit(X_train, y_train)

        # ── 5. Evaluate Model ──────────────────────────────────────────────
        y_pred = clf.predict(X_test)
        self.mae = float(mean_absolute_error(y_test, y_pred))
        self.rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        self.r2_score = float(r2_score(y_test, y_pred))
        self.confidence_score = max(0, min(100, self.r2_score * 100))

        # ── 6. Forecast Future Demand ──────────────────────────────────────
        future_dates = pd.date_range(
            start=self.forecast_start,
            periods=self.horizon_days,
            freq='D',
        )
        future_df = pd.DataFrame({
            'date': future_dates,
            'day_of_week': future_dates.dayofweek,
            'day_of_month': future_dates.day,
            'month': future_dates.month,
            'trend': range(len(df), len(df) + self.horizon_days),
        })
        X_future = future_df[feature_cols].values
        predictions = clf.predict(X_future)
        predictions = np.maximum(predictions, 0)  # No negative demand

        self.forecasted_qty = float(predictions.sum())
        self.forecasted_qty_min = float(max(0, predictions.sum() - predictions.std() * 1.96))
        self.forecasted_qty_max = float(predictions.sum() + predictions.std() * 1.96)

        # ── 7. Store Daily Breakdown ──────────────────────────────────────
        self.daily_forecast_line_ids.unlink()
        lines = []
        for i, (date, qty) in enumerate(zip(future_dates, predictions)):
            lines.append({
                'forecast_id': self.id,
                'forecast_date': date.date(),
                'forecasted_qty': float(qty),
                'day_of_week': date.day_name(),
            })
        self.env['stock.sense.forecast.line'].create(lines)

        _logger.info(
            "Forecast complete for %s: %.2f units over %d days (R²=%.3f)",
            self.product_tmpl_id.name,
            self.forecasted_qty,
            self.horizon_days,
            self.r2_score,
        )

    def action_reset_draft(self):
        self.write({'state': 'draft', 'error_message': False})


class StockSenseForecastLine(models.Model):
    """Daily breakdown of AI forecast results."""
    _name = 'stock.sense.forecast.line'
    _description = 'Stock Sense – Daily Forecast Line'
    _order = 'forecast_date asc'

    forecast_id = fields.Many2one(
        comodel_name='stock.sense.forecast',
        string='Forecast',
        required=True,
        ondelete='cascade',
        index=True,
    )
    forecast_date = fields.Date(string='Date', required=True)
    day_of_week = fields.Char(string='Day')
    forecasted_qty = fields.Float(
        string='Predicted Demand',
        digits='Product Unit of Measure',
    )
    actual_qty = fields.Float(
        string='Actual (if known)',
        digits='Product Unit of Measure',
        default=0.0,
    )
    variance = fields.Float(
        string='Variance',
        compute='_compute_variance',
    )

    @api.depends('forecasted_qty', 'actual_qty')
    def _compute_variance(self):
        for rec in self:
            rec.variance = rec.actual_qty - rec.forecasted_qty
