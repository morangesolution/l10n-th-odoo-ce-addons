# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
import json

import xlsxwriter

from odoo import api, fields, models


class ThTaxReport(models.TransientModel):
    _name = "th.tax.report"
    _description = "Thai VAT Tax Report"

    @api.model
    def get_filter_values(self, start_date, end_date, tax_type, show_cancel):
        """Return VAT invoice lines from account_move_tax_invoice for the given period.

        :param str start_date: ISO date string (YYYY-MM-DD)
        :param str end_date: ISO date string (YYYY-MM-DD)
        :param str tax_type: 'sale' or 'purchase'
        :param bool show_cancel: include cancelled/voided invoices
        :return: dict with keys 'lines', 'total_base', 'total_tax'
        """
        today = fields.Date.today()
        date_from = fields.Date.from_string(start_date) if start_date else today.replace(day=1)
        date_to = fields.Date.from_string(end_date) if end_date else today
        company_id = self.env.company.id
        states = ("posted", "cancel") if show_cancel else ("posted",)
        # When show_cancel=False also hide reversed-but-posted entries (those
        # that would appear as "(VOID)" because their reversing_id is set).
        reversing_clause = "" if show_cancel else "AND t.reversing_id IS NULL"

        self._cr.execute(
            """
            SELECT
                t.partner_id,
                CASE
                    WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                        THEN t.tax_invoice_number
                    ELSE t.tax_invoice_number || ' (VOID)'
                END AS tax_invoice_number,
                TO_CHAR(t.report_date, 'DD/MM/YYYY') AS tax_date,
                CASE WHEN m.ref IS NOT NULL THEN m.ref ELSE ml.move_name END AS doc_ref,
                CASE
                    WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                        THEN t.tax_base_amount
                    ELSE 0.0
                END AS tax_base_amount,
                CASE
                    WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                        THEN t.balance
                    ELSE 0.0
                END AS tax_amount
            FROM account_move_tax_invoice t
            JOIN account_move_line ml ON ml.id = t.move_line_id
            JOIN account_move m ON m.id = ml.move_id
            JOIN account_tax at ON at.id = ml.tax_line_id
            WHERE ml.parent_state IN %%s
                AND t.tax_invoice_number IS NOT NULL
                AND at.type_tax_use = %%s
                AND t.report_date >= %%s
                AND t.report_date <= %%s
                AND ml.company_id = %%s
                AND t.reversed_id IS NULL
                %s
            ORDER BY t.report_date, t.tax_invoice_number
            """ % reversing_clause,
            (states, tax_type, date_from, date_to, company_id),
        )
        rows = self._cr.dictfetchall()

        partner_model = self.env["res.partner"]
        lines = []
        total_base = 0.0
        total_tax = 0.0

        for i, row in enumerate(rows):
            partner = partner_model.browse(row["partner_id"]) if row["partner_id"] else partner_model.browse()
            lines.append({
                "no": i + 1,
                "tax_date": row["tax_date"] or "",
                "tax_invoice_number": row["tax_invoice_number"] or "",
                "partner_name": partner.display_name or "",
                "partner_vat": partner.vat or "",
                "partner_branch": partner.company_registry or "",
                "base_amount": round(row["tax_base_amount"] or 0.0, 2),
                "tax_amount": round(row["tax_amount"] or 0.0, 2),
                "doc_ref": row["doc_ref"] or "",
            })
            total_base += row["tax_base_amount"] or 0.0
            total_tax += row["tax_amount"] or 0.0

        return {
            "lines": lines,
            "total_base": round(total_base, 2),
            "total_tax": round(total_tax, 2),
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
        total_fmt = workbook.add_format({
            "font_size": 10, "border": 1, "bold": True,
            "align": "right", "bg_color": "#f8f9fa",
        })

        # Column widths
        sheet.set_column(0, 0, 5)   # No
        sheet.set_column(1, 1, 14)  # Date
        sheet.set_column(2, 2, 18)  # Tax Inv No
        sheet.set_column(3, 3, 30)  # Partner
        sheet.set_column(4, 4, 14)  # Tax ID
        sheet.set_column(5, 5, 10)  # Branch
        sheet.set_column(6, 6, 14)  # Base Amount
        sheet.set_column(7, 7, 14)  # Tax Amount
        sheet.set_column(8, 8, 16)  # Ref

        sheet.merge_range("A1:I1", report_name, head)
        filters = data.get("filters", {})
        sheet.merge_range(
            "A2:I2",
            f"Period: {filters.get('start_date', '')} to {filters.get('end_date', '')}  "
            f"Type: {(filters.get('tax_type') or '').upper()}",
            workbook.add_format({"align": "center", "font_size": 10}),
        )

        headers = ["No.", "Date", "Tax Inv. No.", "Partner", "Tax ID", "Branch",
                   "Base Amount", "Tax Amount", "Ref"]
        for col, h in enumerate(headers):
            sheet.write(3, col, h, sub_heading)

        row = 4
        for line in data.get("lines", []):
            sheet.write(row, 0, line["no"], txt)
            sheet.write(row, 1, line["tax_date"], txt)
            sheet.write(row, 2, line["tax_invoice_number"], txt)
            sheet.write(row, 3, line["partner_name"], txt)
            sheet.write(row, 4, line["partner_vat"], txt)
            sheet.write(row, 5, line["partner_branch"], txt)
            sheet.write(row, 6, line["base_amount"], txt_right)
            sheet.write(row, 7, line["tax_amount"], txt_right)
            sheet.write(row, 8, line["doc_ref"], txt)
            row += 1

        sheet.write(row, 5, "Total", total_fmt)
        sheet.write(row, 6, data.get("total_base", 0.0), total_fmt)
        sheet.write(row, 7, data.get("total_tax", 0.0), total_fmt)
        sheet.write(row, 8, "", total_fmt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
