from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ocr_service_url = fields.Char(
        string="OCR Service URL",
        config_parameter="l10n_th_ocr.service_url",
        help="URL of the Thai OCR Document Parser microservice (e.g. http://localhost:8001)",
    )
