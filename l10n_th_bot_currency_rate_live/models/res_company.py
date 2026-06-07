# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

CURRENCY_RATE_TYPE = [
    ("mid_rate", "Mid Rate"),
    ("selling", "Selling Rate"),
    ("buying_sight", "Buying Sight Rate"),
    ("buying_transfer", "Buying Transfer Rate"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    bot_token = fields.Char(string="BOT Token")
    bot_rate_type = fields.Selection(
        CURRENCY_RATE_TYPE, string="BOT Rate Type", default="mid_rate"
    )
