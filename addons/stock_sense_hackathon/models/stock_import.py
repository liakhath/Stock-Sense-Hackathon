# -*- coding: utf-8 -*-
import base64
import csv
import io
import json

from odoo import fields, models, _
from odoo.exceptions import AccessError, ValidationError


class StockSenseImportWizard(models.TransientModel):
    _name = 'stock.sense.import.wizard'
    _description = 'Stock Sense Inventory CSV Import'

    file = fields.Binary(required=True)
    filename = fields.Char()
    state = fields.Selection([('upload', 'Upload'), ('validated', 'Validated')], default='upload')
    validation_results = fields.Text(readonly=True)
    parsed_rows = fields.Text(readonly=True)

    def _require_manager(self):
        if not self.env.user.has_group('stock_sense_hackathon.group_stock_sense_manager'):
            raise AccessError(_('Only StockSense Managers can import inventory.'))

    def _parse_and_validate(self):
        self.ensure_one()
        self._require_manager()
        if not self.file:
            raise ValidationError(_('Upload a CSV file first.'))
        try:
            content = base64.b64decode(self.file).decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
        except Exception as exc:
            raise ValidationError(_('The uploaded file is not a valid UTF-8 CSV: %s') % exc) from exc
        required = {'SKU', 'Product', 'Warehouse', 'Quantity', 'Min Stock', 'Unit Cost'}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValidationError(_('CSV must contain these columns: %s') % ', '.join(sorted(required)))
        errors, rows, seen_skus = [], [], set()
        for line_number, row in enumerate(reader, start=2):
            sku = (row.get('SKU') or '').strip()
            name = (row.get('Product') or '').strip()
            warehouse_code = (row.get('Warehouse') or '').strip()
            if not sku:
                errors.append(_('Row %s: SKU is required.') % line_number)
            if not name:
                errors.append(_('Row %s: Product is required.') % line_number)
            if sku in seen_skus:
                errors.append(_('Row %s: Duplicate SKU %s.') % (line_number, sku))
            seen_skus.add(sku)
            warehouse = self.env['stock.warehouse'].search(['|', ('code', '=', warehouse_code), ('name', '=', warehouse_code)], limit=1)
            if not warehouse_code or not warehouse:
                errors.append(_('Row %s: Warehouse %s does not exist.') % (line_number, warehouse_code or _('(blank)')))
            try:
                quantity = float((row.get('Quantity') or '').strip())
                if quantity < 0:
                    raise ValueError
            except ValueError:
                errors.append(_('Row %s: Quantity must be a non-negative number.') % line_number)
                quantity = 0.0
            try:
                minimum = float((row.get('Min Stock') or '').strip())
                if minimum < 0:
                    raise ValueError
            except ValueError:
                errors.append(_('Row %s: Min Stock must be a non-negative number.') % line_number)
                minimum = 0.0
            try:
                unit_cost = float((row.get('Unit Cost') or '').strip())
                if unit_cost < 0:
                    raise ValueError
            except ValueError:
                errors.append(_('Row %s: Unit Cost must be a non-negative number.') % line_number)
                unit_cost = 0.0
            rows.append({'line': line_number, 'sku': sku, 'name': name,
                         'warehouse_id': warehouse.id if warehouse else False,
                         'quantity': quantity, 'minimum': minimum, 'unit_cost': unit_cost})
        if errors:
            raise ValidationError('\n'.join(errors))
        return rows

    def action_validate(self):
        rows = self._parse_and_validate()
        self.write({'parsed_rows': json.dumps(rows), 'validation_results': _('%s row(s) validated successfully.') % len(rows), 'state': 'validated'})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
                'view_mode': 'form', 'target': 'new'}

    def action_import(self):
        self.ensure_one()
        self._require_manager()
        if self.state != 'validated' or not self.parsed_rows:
            raise ValidationError(_('Validate the CSV before importing it.'))
        rows = json.loads(self.parsed_rows)
        for row in rows:
            product = self.env['product.product'].search([('default_code', '=', row['sku'])], limit=1)
            if not product:
                product = self.env['product.product'].create({'name': row['name'], 'default_code': row['sku'], 'standard_price': row['unit_cost']})
            else:
                product.write({'name': row['name'], 'standard_price': row['unit_cost']})
            product.product_tmpl_id.write({'alert_low_stock_threshold': row['minimum']})
            warehouse = self.env['stock.warehouse'].browse(row['warehouse_id'])
            current = self.env['stock.sense.adjustment']._quantity_at_warehouse(product, warehouse)
            self.env['stock.quant'].sudo()._update_available_quantity(product, warehouse.lot_stock_id, row['quantity'] - current)
            self.env['stock.sense.audit.log'].log('IMPORT_COMPLETED', product, current, row['quantity'],
                                                  _('CSV inventory import for warehouse %s.') % warehouse.display_name)
        self.write({'validation_results': _('%s row(s) imported successfully.') % len(rows)})
        return {'type': 'ir.actions.act_window_close'}
