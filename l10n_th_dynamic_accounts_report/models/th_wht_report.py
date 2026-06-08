# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
import json

import xlsxwriter

from odoo import api, fields, models


class ThWhtReport(models.TransientModel):
    _name = "th.wht.report"
    _description = "Thai Withholding Tax Report"

    @api.model
    def get_filter_values(self, start_date, end_date, income_tax_form, show_cancel):
        """Return WHT certificate lines for the given period and PND form.

        :param str start_date: ISO date string (YYYY-MM-DD)
        :param str end_date: ISO date string (YYYY-MM-DD)
        :param str income_tax_form: 'pnd1','pnd2','pnd3','pnd3a','pnd53' or False for all
        :param bool show_cancel: include cancelled certificates
        :return: dict with keys 'lines', 'total_base', 'total_wht'
        """
        today = fields.Date.today()
        date_from = fields.Date.from_string(start_date) if start_date else today.replace(day=1)
        date_to = fields.Date.from_string(end_date) if end_date else today
        company = self.env.company

        domain = [
            ("cert_id.date", ">=", date_from),
            ("cert_id.date", "<=", date_to),
            ("cert_id.company_id", "=", company.id),
            ("cert_id.state", "!=", "draft"),
        ]
        if income_tax_form:
            # pnd1a is a sub-type of pnd1 in the cert model
            form = "pnd1" if income_tax_form == "pnd1a" else income_tax_form
            domain.append(("cert_id.income_tax_form", "=", form))
        if not show_cancel:
            domain.append(("cert_id.state", "!=", "cancel"))

        cert_lines = self.env["withholding.tax.cert.line"].sudo().search(domain)
        income_type_selection = dict(
            self.env["withholding.tax.cert.line"]._fields["wht_cert_income_type"].selection
        )

        lines = []
        total_base = 0.0
        total_wht = 0.0

        for i, line in enumerate(cert_lines):
            cert = line.cert_id
            lines.append({
                "no": i + 1,
                "cert_date": cert.date.strftime("%d/%m/%Y") if cert.date else "",
                "cert_number": cert.number if cert.number != "/" else (cert.name or ""),
                "partner_name": cert.partner_id.display_name or "",
                "partner_vat": cert.partner_id.vat or "",
                "income_type": income_type_selection.get(line.wht_cert_income_type, ""),
                "income_desc": line.wht_cert_income_desc or "",
                "percent": line.wht_percent,
                "base_amount": round(line.base, 2),
                "wht_amount": round(line.amount, 2),
                "is_cancelled": cert.state == "cancel",
            })
            total_base += line.base
            total_wht += line.amount

        return {
            "lines": lines,
            "total_base": round(total_base, 2),
            "total_wht": round(total_wht, 2),
        }

    @api.model
    def get_xlsx_report(self, data, response, report_name, report_action):
        data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet()

        head = workbook.add_format({"font_size": 14, "align": "center", "bold": True})
        sub_heading = workbook.add_format({
            "align": "center", "bold": True, "font_size": 10,
            "border": 1, "bg_color": "#D3D3D3",
        })
        txt = workbook.add_format({"font_size": 10, "border": 1})
        txt_right = workbook.add_format({"font_size": 10, "border": 1, "align": "right"})
        txt_cancel = workbook.add_format({
            "font_size": 10, "border": 1, "font_color": "#999999",
        })
        total_fmt = workbook.add_format({
            "font_size": 10, "border": 1, "bold": True,
            "align": "right", "bg_color": "#f8f9fa",
        })

        sheet.set_column(0, 0, 5)   # No
        sheet.set_column(1, 1, 14)  # Cert Date
        sheet.set_column(2, 2, 18)  # Cert No
        sheet.set_column(3, 3, 30)  # Vendor
        sheet.set_column(4, 4, 14)  # Tax ID
        sheet.set_column(5, 5, 40)  # Income Type
        sheet.set_column(6, 6, 8)   # %
        sheet.set_column(7, 7, 14)  # Base Amount
        sheet.set_column(8, 8, 14)  # WHT Amount

        filters = data.get("filters", {})
        sheet.merge_range("A1:I1", report_name, head)
        sheet.merge_range(
            "A2:I2",
            f"Period: {filters.get('start_date', '')} to {filters.get('end_date', '')}  "
            f"PND Form: {(filters.get('income_tax_form') or 'All').upper()}",
            workbook.add_format({"align": "center", "font_size": 10}),
        )

        headers = ["No.", "Cert Date", "Cert No.", "Vendor", "Tax ID",
                   "Income Type", "% Tax", "Base Amount", "WHT Amount"]
        for col, h in enumerate(headers):
            sheet.write(3, col, h, sub_heading)

        row = 4
        for line in data.get("lines", []):
            fmt = txt_cancel if line.get("is_cancelled") else txt
            fmt_r = txt_cancel if line.get("is_cancelled") else txt_right
            sheet.write(row, 0, line["no"], fmt)
            sheet.write(row, 1, line["cert_date"], fmt)
            sheet.write(row, 2, line["cert_number"], fmt)
            sheet.write(row, 3, line["partner_name"], fmt)
            sheet.write(row, 4, line["partner_vat"], fmt)
            sheet.write(row, 5, line["income_type"], fmt)
            sheet.write(row, 6, line["percent"], fmt_r)
            sheet.write(row, 7, line["base_amount"], fmt_r)
            sheet.write(row, 8, line["wht_amount"], fmt_r)
            row += 1

        sheet.write(row, 6, "Total", total_fmt)
        sheet.write(row, 7, data.get("total_base", 0.0), total_fmt)
        sheet.write(row, 8, data.get("total_wht", 0.0), total_fmt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
