# Copyright 2025 Morange Solution Co., Ltd. (https://www.morange.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Dynamic Accounts Report - Thai Tax",
    "version": "18.0.1.0.0",
    "author": "Morange Solution Co., Ltd.",
    "website": "https://www.morange.co.th",
    "license": "AGPL-3",
    "category": "Accounting/Accounting",
    "depends": [
        "dynamic_accounts_report",
        "l10n_th_account_tax",
    ],
    "data": [
        "views/accounting_report_views.xml",
        "report/th_tax_report_templates.xml",
        "report/th_wht_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_th_dynamic_accounts_report/static/src/js/th_tax_report.js",
            "l10n_th_dynamic_accounts_report/static/src/js/th_wht_report.js",
            "l10n_th_dynamic_accounts_report/static/src/xml/th_tax_report_views.xml",
            "l10n_th_dynamic_accounts_report/static/src/xml/th_wht_report_views.xml",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
