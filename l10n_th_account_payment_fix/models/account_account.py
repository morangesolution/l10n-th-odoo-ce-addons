from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    # Odoo 18 moved company_id → company_ids (Many2many).
    # Some OCA modules (e.g. account_payment_multi_deduction) still use
    # check_company=True on Many2one fields pointing to account.account.
    # That causes Odoo's web_read to request company_id from account.account,
    # resulting in KeyError: 'company_id'.  This computed shim satisfies the
    # read without breaking any write paths.
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company_id",
        store=False,
        readonly=True,
    )

    @api.depends("company_ids")
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.company_ids[:1]
