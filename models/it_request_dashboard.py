from odoo import api, fields, models


class ITRequestDashboard(models.Model):
    _name = "it.request.dashboard"
    _description = "IT Request Dashboard"

    # ---------------------------------------------------------
    # REQUEST KPI FIELDS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # EQUIPMENT KPI FIELDS
    # ---------------------------------------------------------

    total_equipment = fields.Integer(
        string="Total Equipment",
        compute="_compute_dashboard_counts",
    )

    available_equipment = fields.Integer(
        string="Available Equipment",
        compute="_compute_dashboard_counts",
    )

    assigned_equipment = fields.Integer(
        string="Assigned Equipment",
        compute="_compute_dashboard_counts",
    )

    maintenance_equipment = fields.Integer(
        string="Maintenance Equipment",
        compute="_compute_dashboard_counts",
    )

    # ---------------------------------------------------------
    # KPI COMPUTATION
    # ---------------------------------------------------------

    @api.depends()
    def _compute_dashboard_counts(self):
        request_model = self.env["it.request"]
        equipment_model = self.env["it.equipment"]

        # REQUEST COUNTS

        total_requests = request_model.search_count([])

        open_requests = request_model.search_count(
            [
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                )
            ]
        )

        critical_requests = request_model.search_count(
            [
                ("priority", "=", "critical"),
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                ),
            ]
        )

        overdue_requests = request_model.search_count(
            [
                ("is_overdue", "=", True),
            ]
        )

        # EQUIPMENT COUNTS

        total_equipment = equipment_model.search_count([])

        available_equipment = equipment_model.search_count(
            [
                ("status", "=", "available"),
            ]
        )

        assigned_equipment = equipment_model.search_count(
            [
                ("status", "=", "assigned"),
            ]
        )

        maintenance_equipment = equipment_model.search_count(
            [
                ("status", "=", "maintenance"),
            ]
        )

        for record in self:
            record.total_requests = total_requests
            record.open_requests = open_requests
            record.critical_requests = critical_requests
            record.overdue_requests = overdue_requests

            record.total_equipment = total_equipment
            record.available_equipment = available_equipment
            record.assigned_equipment = assigned_equipment
            record.maintenance_equipment = maintenance_equipment

    # ---------------------------------------------------------
    # GENERIC REQUEST ACTION
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

    # ---------------------------------------------------------
    # REQUEST ACTIONS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # GENERIC EQUIPMENT ACTION
    # ---------------------------------------------------------

    def _get_equipment_action(self, name, domain):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "it.equipment",
            "view_mode": "list,form",
            "domain": domain,
            "target": "current",
        }

    # ---------------------------------------------------------
    # EQUIPMENT ACTIONS
    # ---------------------------------------------------------

    def action_view_all_equipment(self):
        return self._get_equipment_action(
            "All Equipment",
            [],
        )

    def action_view_available_equipment(self):
        return self._get_equipment_action(
            "Available Equipment",
            [
                ("status", "=", "available"),
            ],
        )

    def action_view_assigned_equipment(self):
        return self._get_equipment_action(
            "Assigned Equipment",
            [
                ("status", "=", "assigned"),
            ],
        )

    def action_view_maintenance_equipment(self):
        return self._get_equipment_action(
            "Equipment in Maintenance",
            [
                ("status", "=", "maintenance"),
            ],
        )