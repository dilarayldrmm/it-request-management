from odoo import api, fields, models


class ITRequestDashboard(models.Model):
    _name = "it.request.dashboard"
    _description = "IT Request Dashboard"

    total_requests = fields.Integer(
        string="Total Requests",
        compute="_compute_dashboard_counts",
    )

    open_requests = fields.Integer(
        string="Open Requests",
        compute="_compute_dashboard_counts",
    )

    critical_requests = fields.Integer(
        string="Critical Requests",
        compute="_compute_dashboard_counts",
    )

    overdue_requests = fields.Integer(
        string="Overdue Requests",
        compute="_compute_dashboard_counts",
    )

    @api.depends()
    def _compute_dashboard_counts(self):
        request_model = self.env["it.request"]

        total = request_model.search_count([])

        open_count = request_model.search_count(
            [
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                )
            ]
        )

        critical_count = request_model.search_count(
            [
                ("priority", "=", "critical"),
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                ),
            ]
        )

        overdue_count = request_model.search_count(
            [
                ("is_overdue", "=", True),
            ]
        )

        for record in self:
            record.total_requests = total
            record.open_requests = open_count
            record.critical_requests = critical_count
            record.overdue_requests = overdue_count

    # ---------------------------------------------------------
    # DASHBOARD ACTIONS
    # ---------------------------------------------------------

    def _get_request_action(self, name, domain):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "it.request",
            "view_mode": "kanban,list,form",
            "domain": domain,
            "target": "current",
        }

    def action_view_all_requests(self):
        return self._get_request_action(
            "All IT Requests",
            [],
        )

    def action_view_open_requests(self):
        return self._get_request_action(
            "Open IT Requests",
            [
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                )
            ],
        )

    def action_view_critical_requests(self):
        return self._get_request_action(
            "Critical IT Requests",
            [
                ("priority", "=", "critical"),
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                ),
            ],
        )

    def action_view_overdue_requests(self):
        return self._get_request_action(
            "Overdue IT Requests",
            [
                ("is_overdue", "=", True),
            ],
        )