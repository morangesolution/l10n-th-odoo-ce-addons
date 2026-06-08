# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_currency_rate_inverted = fields.Float(
        string="Currency Rate",
        compute="_compute_invoice_currency_rate_inverted",
        inverse="_inverse_invoice_currency_rate_inverted",
        digits=(12, 6),
    )

    @api.depends("invoice_currency_rate")
    def _compute_invoice_currency_rate_inverted(self):
        for move in self:
            move.invoice_currency_rate_inverted = (
                1.0 / move.invoice_currency_rate if move.invoice_currency_rate else 0.0
            )

    def _inverse_invoice_currency_rate_inverted(self):
        for move in self:
            if move.invoice_currency_rate_inverted:
                move.invoice_currency_rate = 1.0 / move.invoice_currency_rate_inverted
