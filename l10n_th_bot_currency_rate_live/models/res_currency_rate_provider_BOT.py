# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ResCurrencyRateProviderBOT(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("BOT", "Bank of Thailand")],
        ondelete={"BOT": "set default"},
    )

    @api.depends("service")
    def _compute_available_currency_ids(self):
        res = super()._compute_available_currency_ids()
        Currency = self.env["res.currency"]
        for provider in self:
            if provider.service == "BOT":
                provider.available_currency_ids = Currency.search(
                    [("bot_currency_name", "in", provider._get_supported_currencies())]
                )
        return res

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "BOT":
            return super()._get_supported_currencies()

        # List of currencies obrained from:
        # https://apigw1.bot.or.th/bot/public/Stat-ExchangeRate/v2
        return [
            "USD",
            "GBP",
            "EUR",
            "JPY",
            "HKD",
            "MYR",
            "SGD",
            "BND",
            "PHP",
            "IDR",
            "INR",
            "CHF",
            "AUD",
            "NZD",
            "CAD",
            "SEK",
            "DKK",
            "NOK",
            "CNY",
            "MXN",
            "ZAR",
            "KRW",
            "TWD",
            "KWD",
            "SAR",
            "AED",
            "MMK",
            "BDT",
            "CZK",
            "KHR",
            "KES",
            "LAK",
            "RUB",
            "VND",
            "EGP",
            "PLN",
            "LKR",
            "IQD",
            "BHD",
            "OMR",
            "JOD",
            "QAR",
            "MVR",
            "NPR",
            "PGK",
            "ILS",
            "HUF",
            "PKR",
        ]

    def _get_currency_unit(self, bot_currency_name):
        return 100.0 if bot_currency_name == "JPY" else 1.0

    def _update_content_currency_update(
        self, bot_currency, content, result, date_from, date_to, rate_type=None
    ):
        data = result["data"]
        last_updated = data["data_header"]["last_updated"]
        date_last_update = datetime.datetime.strptime(last_updated, "%Y-%m-%d").date()
        if date_from > date_last_update and date_to > date_last_update:
            raise UserError(self.env._(f"BOT Last Updated: {last_updated}"))
        effective_rate_type = rate_type or bot_currency.bot_currency_rate_type
        unit = self._get_currency_unit(bot_currency.bot_currency_name)
        for data_detail in data["data_detail"]:
            period = (
                fields.Date.from_string(data_detail["period"]).strftime(
                    DEFAULT_SERVER_DATE_FORMAT
                )
                if data_detail["period"]
                else False
            )
            rate_value = data_detail.get(effective_rate_type)
            if not period or not rate_value:
                continue
            rate = unit / float(rate_value)
            if period in content:
                content[period][bot_currency.name] = rate
            else:
                content[period] = {bot_currency.name: rate}

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "BOT":
            if base_currency != "THB":
                raise UserError(
                    self.env._(
                        "Bank of Thailand is suitable only for companies with THB as "
                        "base currency!"
                    )
                )
            ICP = self.env["ir.config_parameter"].sudo()
            bot_token = self.company_id.bot_token
            if not bot_token:
                raise UserError(self.env._("No bot.or.th credentials specified!"))
            hostname = ICP.get_param("hostname_TH_BOT")
            route_BOT = ICP.get_param("route_TH_BOT_exchange_daily")
            default_url = "{}{}/?start_period={}&end_period={}".format(
                hostname,
                route_BOT,
                date_from.strftime("%Y-%m-%d"),
                date_to.strftime("%Y-%m-%d"),
            )
            headers = {
                "Authorization": bot_token,
                "accept": "application/json",
                "Content-Type": "application/json",
            }
            bot_currencies = self.env["res.currency"].search(
                [("name", "in", currencies)]
            )
            global_rate_type = self.company_id.bot_rate_type
            content = {}
            for bot_currency in bot_currencies:
                currency = bot_currency.bot_currency_name
                url = f"{default_url}&currency={currency}"
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    data_dict = response.json()
                except Exception as e:
                    raise UserError(self.env._(f"BOT API request failed: {e}")) from e
                result = data_dict.get("result", False)
                if not result:
                    raise UserError(
                        self.env._(
                            f"httpCode: {data_dict.get('httpCode')}\n"
                            f"moreInformation: {data_dict.get('moreInformation')}"
                        )
                    )
                self._update_content_currency_update(
                    bot_currency, content, result, date_from, date_to,
                    rate_type=global_rate_type,
                )
                # Fallback: if no rate added (e.g. weekend/holiday), retry with last_updated date
                if not any(bot_currency.name in d for d in content.values()):
                    last_updated_str = result["data"]["data_header"]["last_updated"]
                    last_updated_date = datetime.datetime.strptime(
                        last_updated_str, "%Y-%m-%d"
                    ).date()
                    fallback_url = (
                        f"{hostname}{route_BOT}/?start_period={last_updated_str}"
                        f"&end_period={last_updated_str}&currency={currency}"
                    )
                    try:
                        fb_response = requests.get(fallback_url, headers=headers, timeout=15)
                        fb_result = fb_response.json().get("result", False)
                    except Exception:
                        fb_result = False
                    if fb_result:
                        self._update_content_currency_update(
                            bot_currency, content, fb_result,
                            last_updated_date, last_updated_date,
                            rate_type=global_rate_type,
                        )
            return content
        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
