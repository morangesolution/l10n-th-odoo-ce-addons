/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

const actionRegistry = registry.category("actions");
const today = luxon.DateTime.now();

class ThWhtReport extends owl.Component {
    async setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");
        this.start_date = useRef("date_from");
        this.end_date = useRef("date_to");
        this.state = useState({
            data: null,
            income_tax_form: "pnd3",
            show_cancel: false,
            date_range: "month",
        });
        this.load_data();
    }

    async load_data() {
        const startOfMonth = today.startOf("month").toFormat("yyyy-MM-dd");
        const endOfMonth = today.endOf("month").toFormat("yyyy-MM-dd");
        if (this.start_date.el) {
            this.start_date.el.value = startOfMonth;
            this.end_date.el.value = endOfMonth;
        }
        await this._fetchData(startOfMonth, endOfMonth);
    }

    async _fetchData(start, end) {
        this.state.data = await this.orm.call(
            "th.wht.report",
            "get_filter_values",
            [start, end, this.state.income_tax_form, this.state.show_cancel]
        );
    }

    async applyFilter(ev) {
        const val = ev.target.attributes["data-value"]
            ? ev.target.attributes["data-value"].value
            : ev.target.name;

        if (val === "month") {
            this.start_date.el.value = today.startOf("month").toFormat("yyyy-MM-dd");
            this.end_date.el.value = today.endOf("month").toFormat("yyyy-MM-dd");
            this.state.date_range = "month";
        } else if (val === "quarter") {
            this.start_date.el.value = today.startOf("quarter").toFormat("yyyy-MM-dd");
            this.end_date.el.value = today.endOf("quarter").toFormat("yyyy-MM-dd");
            this.state.date_range = "quarter";
        } else if (val === "year") {
            this.start_date.el.value = today.startOf("year").toFormat("yyyy-MM-dd");
            this.end_date.el.value = today.endOf("year").toFormat("yyyy-MM-dd");
            this.state.date_range = "year";
        } else if (val === "last-month") {
            const last = today.startOf("month").minus({ days: 1 });
            this.start_date.el.value = last.startOf("month").toFormat("yyyy-MM-dd");
            this.end_date.el.value = last.toFormat("yyyy-MM-dd");
            this.state.date_range = "last-month";
        } else if (val === "last-quarter") {
            const last = today.startOf("quarter").minus({ days: 1 });
            this.start_date.el.value = last.startOf("quarter").toFormat("yyyy-MM-dd");
            this.end_date.el.value = last.toFormat("yyyy-MM-dd");
            this.state.date_range = "last-quarter";
        } else if (val === "last-year") {
            const last = today.startOf("year").minus({ days: 1 });
            this.start_date.el.value = last.startOf("year").toFormat("yyyy-MM-dd");
            this.end_date.el.value = last.toFormat("yyyy-MM-dd");
            this.state.date_range = "last-year";
        } else if (["pnd1", "pnd1a", "pnd2", "pnd3", "pnd3a", "pnd53", "all"].includes(val)) {
            this.state.income_tax_form = val === "all" ? false : val;
        } else if (val === "show_cancel") {
            this.state.show_cancel = !this.state.show_cancel;
            ev.target.classList.toggle("selected-filter");
        }

        await this._fetchData(this.start_date.el.value, this.end_date.el.value);
    }

    async applyDateInput(ev) {
        await this._fetchData(this.start_date.el.value, this.end_date.el.value);
    }

    get pndLabel() {
        const map = {
            pnd1: "PND1", pnd1a: "PND1A", pnd2: "PND2",
            pnd3: "PND3", pnd3a: "PND3A", pnd53: "PND53",
        };
        return this.state.income_tax_form ? (map[this.state.income_tax_form] || "All") : "All";
    }

    _buildPrintData() {
        return {
            lines: this.state.data ? this.state.data.lines : [],
            total_base: this.state.data ? this.state.data.total_base : 0,
            total_wht: this.state.data ? this.state.data.total_wht : 0,
            filters: {
                start_date: this.start_date.el ? this.start_date.el.value : "",
                end_date: this.end_date.el ? this.end_date.el.value : "",
                income_tax_form: this.state.income_tax_form,
                show_cancel: this.state.show_cancel,
            },
            title: this.props.action.display_name,
        };
    }

    async printPdf(ev) {
        ev.preventDefault();
        return this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "l10n_th_dynamic_accounts_report.th_wht_report",
            report_file: "l10n_th_dynamic_accounts_report.th_wht_report",
            data: this._buildPrintData(),
            display_name: this.props.action.display_name,
        });
    }

    async print_xlsx() {
        const action = {
            data: {
                model: "th.wht.report",
                data: JSON.stringify(this._buildPrintData()),
                output_format: "xlsx",
                report_action: this.props.action.id,
                report_name: this.props.action.display_name,
            },
        };
        BlockUI;
        await download({
            url: "/xlsx_report",
            data: action.data,
            complete: () => {},
            error: (error) => this.call("crash_manager", "rpc_error", error),
        });
    }

    formatAmount(value) {
        if (value === undefined || value === null) return "";
        return Number(value).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
}

ThWhtReport.template = "th_wht_r_template";
actionRegistry.add("th_wht_r", ThWhtReport);
