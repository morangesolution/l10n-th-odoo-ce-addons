# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bot_token = fields.Char(related="company_id.bot_token", readonly=False, string="Bot Token")
    bot_rate_type = fields.Selection(
        related="company_id.bot_rate_type", readonly=False, string="BOT Rate Type"
    )
