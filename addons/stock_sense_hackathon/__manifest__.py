# -*- coding: utf-8 -*-
{
    'name': '🧠 Stock Sense – AI-Powered Inventory Intelligence',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'AI-powered stock forecasting, IoT-based monitoring, and smart replenishment for Odoo 17',
    'description': """
        Stock Sense Hackathon Module
        ============================
        An intelligent inventory management extension for Odoo 17 that combines:
        - AI/ML demand forecasting (Scikit-learn, Pandas)
        - IoT real-time stock monitoring (Raspberry Pi integration)
        - Smart replenishment suggestions
        - Advanced stock alert system
        - Interactive analytics dashboard
    """,
    'author': 'Stock Sense Team',
    'website': 'https://github.com/liakhath/Stock-Sense-Hackathon',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'product',
        'purchase',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/stock_sense_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/stock_sense_data.xml',
        # Views
        'views/stock_sense_views.xml',
        'views/stock_forecast_views.xml',
        'views/stock_alert_views.xml',
        'views/stock_adjustment_views.xml',
        'views/stock_adjustment_reject_wizard_views.xml',
        'views/stock_reorder_views.xml',
        'views/stock_audit_views.xml',
        'views/stock_import_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_sense_hackathon/static/src/css/stock_sense.css',
            'stock_sense_hackathon/static/src/js/stock_dashboard.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'images': ['static/description/banner.png'],
}
