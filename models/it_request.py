from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class ITRequest(models.Model):
    _name = "it.request"
    _description = "IT Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]

   

    reference = fields.Char(
        string="Request No",
        required=True,
        readonly=True,
        copy=False,
        default="New",
    )

    requester_id = fields.Many2one(
        "res.users",
        string="Requester",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )

    assigned_to_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        tracking=True,
    )

    title = fields.Char(
        string="Title",
        required=True,
    )

    description = fields.Text(
        string="Description",
    )

    category_id = fields.Many2one(
        "it.request.category",
        string="Category",
        required=True,
        tracking=True,
    )

    equipment_id = fields.Many2one(
       "it.equipment",
        string="Related Equipment",
    )

    maintenance_ids = fields.One2many(
        "it.equipment.maintenance",
        "request_id",
        string="Maintenances",
    )

    maintenance_count = fields.Integer(
        string="Maintenance Count",
        compute="_compute_maintenance_count",
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Priority",
        default="medium",
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        group_expand=True,
    )

    resolution_note = fields.Text(
        string="Resolution Note",
    )

    submitted_at = fields.Datetime(
        string="Submitted At",
        readonly=True,
    )

    started_at = fields.Datetime(
        string="Started At",
        readonly=True,
    )

    resolved_at = fields.Datetime(
        string="Resolved At",
        readonly=True,
    )

    closed_at = fields.Datetime(
        string="Closed At",
        readonly=True,
    )

    deadline = fields.Datetime(
        string="Deadline",
        compute="_compute_deadline",
        store=True,
    )

    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
    )

   

    @api.depends("priority", "create_date")
    def _compute_deadline(self):
        hours_by_priority = {
            "low": 72,
            "medium": 48,
            "high": 24,
            "critical": 4,
        }

        for record in self:
            if record.create_date and record.priority:
                hours = hours_by_priority.get(
                    record.priority,
                    48,
                )

                record.deadline = (
                    record.create_date
                    + timedelta(hours=hours)
                )

            else:
                record.deadline = False

    @api.depends("maintenance_ids")
    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = len(
                record.maintenance_ids
            )

    @api.depends("deadline", "state")
    def _compute_is_overdue(self):
        now = fields.Datetime.now()

        for record in self:
            record.is_overdue = bool(
                record.deadline
                and record.deadline < now
                and record.state not in (
                    "resolved",
                    "closed",
                )
            )

    def _search_is_overdue(self, operator, value):
        if operator not in ("=", "!="):
            raise NotImplementedError(
                "Only '=' and '!=' operators are supported."
            )

        want_overdue = bool(value)

        if operator == "!=":
            want_overdue = not want_overdue

        now = fields.Datetime.now()

        if want_overdue:
            return [
                ("deadline", "!=", False),
                ("deadline", "<", now),
                (
                    "state",
                    "not in",
                    ["resolved", "closed"],
                ),
            ]

        return [
            "|",
            "|",
            ("deadline", "=", False),
            ("deadline", ">=", now),
            (
                "state",
                "in",
                ["resolved", "closed"],
            ),
        ]

    def action_create_maintenance(self):
        self.ensure_one()

        if not self.equipment_id:
            raise UserError(
                "Please select related equipment before creating maintenance."
            )

        issue_description = self.title
        if self.description:
            issue_description = (
                f"{self.title}\n\n{self.description}"
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Create Maintenance",
            "res_model": "it.equipment.maintenance",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_equipment_id": self.equipment_id.id,
                "default_request_id": self.id,
                "default_issue_description": issue_description,
            },
        }

    def action_view_maintenances(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": f"Maintenances - {self.reference}",
            "res_model": "it.equipment.maintenance",
            "view_mode": "list,form",
            "domain": [
                ("request_id", "=", self.id),
            ],
            "context": {
                "default_request_id": self.id,
                "default_equipment_id": (
                    self.equipment_id.id
                    if self.equipment_id
                    else False
                ),
            },
            "target": "current",
        }

   

    def _sync_assignment_activity(self):
        activity_xmlid = (
            "it_request_management."
            "mail_activity_type_it_request_assignment"
        )

        for record in self:
            record_sudo = record.sudo()

            assignment_activities = (
                record_sudo.activity_search(
                    [activity_xmlid]
                )
            )

            # Request artık kimseye atanmamışsa
            # eski assignment activity'sini kaldır.
            if not record_sudo.assigned_to_id:
                if assignment_activities:
                    assignment_activities.unlink()

                continue

            summary = (
                f"{record_sudo.reference} - "
                f"{record_sudo.title}"
            )

            note = (
                "A new IT request has been assigned "
                f"to you: {record_sudo.reference} - "
                f"{record_sudo.title}"
            )

            # Daha önce oluşturulmuş assignment activity varsa
            # yenisini oluşturmak yerine güncelle.
            if assignment_activities:
                assignment_activities.write(
                    {
                        "user_id": (
                            record_sudo.assigned_to_id.id
                        ),
                        "summary": summary,
                        "note": note,
                        "date_deadline": (
                            fields.Date.context_today(
                                record_sudo
                            )
                        ),
                    }
                )

            # İlk defa atanıyorsa yeni activity oluştur.
            else:
                record_sudo.activity_schedule(
                    activity_xmlid,
                    user_id=(
                        record_sudo.assigned_to_id.id
                    ),
                    summary=summary,
                    note=note,
                    date_deadline=(
                        fields.Date.context_today(
                            record_sudo
                        )
                    ),
                )

    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = (
                    self.env["ir.sequence"]
                    .next_by_code("it.request")
                    or "New"
                )

        records = super().create(vals_list)

        assigned_records = records.filtered(
            "assigned_to_id"
        )

        if assigned_records:
            assigned_records._sync_assignment_activity()

        return records

   

    def write(self, vals):
        result = super().write(vals)

        if "assigned_to_id" in vals:
            self._sync_assignment_activity()

        return result

  
    def action_submit(self):
        self.write(
            {
                "state": "submitted",
                "submitted_at": fields.Datetime.now(),
            }
        )

    def action_start(self):
        if not self.assigned_to_id:
            raise UserError(
                "Please assign the request to someone "
                "before starting."
            )

        self.write(
            {
                "state": "in_progress",
                "started_at": fields.Datetime.now(),
            }
        )

    def action_resolve(self):
        if not self.resolution_note:
            raise UserError(
                "Please enter a resolution note "
                "before resolving the request."
            )

        self.write(
            {
                "state": "resolved",
                "resolved_at": fields.Datetime.now(),
            }
        )

        self.sudo().activity_feedback(
            [
                "it_request_management."
                "mail_activity_type_it_request_assignment"
            ],
            feedback="IT request resolved.",
        )

    def action_close(self):
        self.write(
            {
                "state": "closed",
                "closed_at": fields.Datetime.now(),
            }
        )