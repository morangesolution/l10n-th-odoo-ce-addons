# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Currency Rate Update - BOT",
    "version": "18.0.1.3.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "depends": [
        "currency_rate_update",
    ],
    "data": [
        "data/config_parameter.xml",
        "data/res_currency_rate_provider.xml",
        "views/res_currency_views.xml",
        "views/res_config_settings.xml",
        "views/res_currency_rate_provider.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
