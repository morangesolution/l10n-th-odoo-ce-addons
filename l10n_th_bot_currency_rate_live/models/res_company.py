# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .res_currency import CURRENCY_RATE_TYPE


class ResCompany(models.Model):
    _inherit = "res.company"

    bot_token = fields.Char(string="BOT Token")
    bot_rate_type = fields.Selection(
        CURRENCY_RATE_TYPE, string="BOT Rate Type"
    )
