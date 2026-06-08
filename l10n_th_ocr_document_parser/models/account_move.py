import base64
import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_IMAGE_MIMETYPES = {"image/png", "image/jpeg", "image/jpg"}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_edi_decoder(self, file_data, new=False):
        mimetype = ""
        if file_data.get("attachment"):
            mimetype = file_data["attachment"].mimetype or ""

        is_pdf = file_data.get("type") == "pdf"
        is_image = mimetype in _IMAGE_MIMETYPES

        if is_pdf or is_image:
            service_url = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_th_ocr.service_url")
            )
            if service_url:
                return self._make_ocr_decoder(service_url)

        return super()._get_edi_decoder(file_data, new=new)

    def _make_ocr_decoder(self, service_url):
        def ocr_decoder(invoice, file_data, new):
            content = file_data.get("content", b"")
            content_b64 = base64.b64encode(content).decode()
            mimetype = "application/pdf"
            if file_data.get("attachment"):
                mimetype = file_data["attachment"].mimetype or mimetype

            try:
                resp = requests.post(
                    f"{service_url.rstrip('/')}/extract",
                    json={
                        "content": content_b64,
                        "filename": file_data.get("filename", "document"),
                        "mimetype": mimetype,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                _logger.warning("OCR service error: %s", e)
                return False

            if not data or data.get("confidence", 0) < 0.3:
                _logger.info(
                    "OCR returned low confidence (%.2f), skipping fill",
                    data.get("confidence", 0) if data else 0,
                )
                return False

            return invoice._apply_ocr_result(data, new)

        return ocr_decoder

    def _apply_ocr_result(self, data, new):
        # --- Partner ---
        partner = None
        vendor_vat = (data.get("vendor_vat") or "").strip()
        vendor_name = (data.get("vendor_name") or "").strip()

        if vendor_vat:
            partner = self.env["res.partner"].sudo().search(
                [("vat", "=", vendor_vat), ("is_company", "=", True)], limit=1
            )
        if not partner and vendor_name:
            partner = self.env["res.partner"].sudo().search(
                [("name", "ilike", vendor_name), ("is_company", "=", True)], limit=1
            )

        vals = {}
        if partner:
            vals["partner_id"] = partner.id

        # --- Dates ---
        invoice_date = data.get("invoice_date")
        if invoice_date:
            try:
                fields.Date.from_string(invoice_date)
                vals["invoice_date"] = invoice_date
            except Exception:
                pass

        due_date = data.get("due_date")
        if due_date:
            try:
                fields.Date.from_string(due_date)
                vals["invoice_date_due"] = due_date
            except Exception:
                pass

        invoice_number = data.get("invoice_number")
        if invoice_number:
            vals["ref"] = invoice_number

        if vals:
            self.write(vals)

        # --- Invoice lines ---
        lines = data.get("lines") or []
        if lines:
            self._create_ocr_invoice_lines(lines)

        return True

    def _create_ocr_invoice_lines(self, lines):
        company = self.company_id
        line_vals_list = []

        for item in lines:
            description = (item.get("description") or "").strip()
            quantity = float(item.get("quantity") or 1)
            unit_price = float(item.get("unit_price") or 0)
            tax_percent = item.get("tax_percent")

            # Match product by name
            product = None
            if description:
                product = self.env["product.product"].sudo().search(
                    [("name", "ilike", description)], limit=1
                )

            # Match tax by percent
            taxes = self.env["account.tax"]
            if tax_percent is not None:
                taxes = self.env["account.tax"].sudo().search(
                    [
                        ("amount", "=", float(tax_percent)),
                        ("type_tax_use", "in", ("purchase", "all")),
                        ("company_id", "=", company.id),
                    ],
                    limit=1,
                )

            line_val = {
                "move_id": self.id,
                "name": description or (product.name if product else "/"),
                "quantity": quantity,
                "price_unit": unit_price,
            }
            if product:
                line_val["product_id"] = product.id
            if taxes:
                line_val["tax_ids"] = [fields.Command.set(taxes.ids)]

            # Determine account
            account = None
            if product:
                account = product.product_tmpl_id._get_product_accounts().get("expense")
            if not account:
                account = self.env["account.account"].sudo().search(
                    [
                        ("company_id", "=", company.id),
                        ("account_type", "=", "expense"),
                        ("deprecated", "=", False),
                    ],
                    limit=1,
                )
            if account:
                line_val["account_id"] = account.id

            line_vals_list.append(line_val)

        if line_vals_list:
            # Remove placeholder empty lines added by Odoo on new invoice
            self.invoice_line_ids.filtered(
                lambda l: not l.product_id and not l.name and l.price_unit == 0
            ).unlink()
            self.env["account.move.line"].sudo().create(line_vals_list)
