from datetime import timedelta
from odoo import api, fields, models

class ITEquipmentMaintenance(models.Model):
    _name = "it.equipment.maintenance"
    _description = "IT Equipment Maintenance"
    _order = "maintenance_date desc, id desc"

    equipment_id = fields.Many2one(
        "it.equipment",
        string="Equipment",
        required=True,
        ondelete="cascade",
    )

    request_id = fields.Many2one(
        "it.request",
        string="Related IT Request",
        ondelete="set null",
    )

    maintenance_date = fields.Date(
        string="Maintenance Date",
        required=True,
        default=fields.Date.context_today,
    )

    technician_id = fields.Many2one(
        "res.users",
        string="Technician",
        default=lambda self: self.env.user,
    )

    issue_description = fields.Text(
        string="Issue Description",
        required=True,
    )

    action_taken = fields.Text(
        string="Action Taken",
    )

    status = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="scheduled",
    )

    planning_status = fields.Selection(
        [
            ("overdue", "Overdue"),
            ("due_soon", "Due Soon"),
            ("planned", "Planned"),
            ("not_scheduled", "Not Scheduled"),
        ],
        string="Planning Status",
        compute="_compute_planning_info",
        search="_search_planning_status",
    )

    days_until_maintenance = fields.Integer(
        string="Days Until Maintenance",
        compute="_compute_planning_info",
    )

    cost = fields.Float(
        string="Maintenance Cost",
    )

    note = fields.Text(
        string="Notes",
    )

    # ---------------------------------------------------------
    # EQUIPMENT STATUS SYNCHRONIZATION
    # ---------------------------------------------------------

    def _sync_equipment_status(self, equipments):
        for equipment in equipments:
            # Retired equipment should remain retired.
            if equipment.status == "retired":
                continue

            in_progress_count = self.search_count(
                [
                    ("equipment_id", "=", equipment.id),
                    ("status", "=", "in_progress"),
                ]
            )

            if in_progress_count:
                equipment.write(
                    {
                        "status": "maintenance",
                    }
                )

            elif equipment.assigned_to_id:
                equipment.write(
                    {
                        "status": "assigned",
                    }
                )

            else:
                equipment.write(
                    {
                        "status": "available",
                    }
                )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        equipments = records.mapped("equipment_id")

        records._sync_equipment_status(equipments)

        return records

    # ---------------------------------------------------------
    # WRITE
    # ---------------------------------------------------------

    def write(self, vals):
        old_equipments = self.mapped("equipment_id")

        result = super().write(vals)

        new_equipments = self.mapped("equipment_id")

        equipments = old_equipments | new_equipments

        self._sync_equipment_status(equipments)

        return result

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def unlink(self):
        equipments = self.mapped("equipment_id")

        result = super().unlink()

        self._sync_equipment_status(equipments)

        return result

    @api.depends("maintenance_date", "status")
    def _compute_planning_info(self):
        today = fields.Date.context_today(self)
        due_soon_limit = today + timedelta(days=30)
        for record in self:
            record.days_until_maintenance = 0
            if (
                record.status != "scheduled"
                or not record.maintenance_date
            ):
                record.planning_status = "not_scheduled"
                continue
            days_left = (record.maintenance_date - today).days
            record.days_until_maintenance = days_left
            if record.maintenance_date < today:
                record.planning_status = "overdue"
            elif record.maintenance_date <= due_soon_limit:
                record.planning_status = "due_soon"
            else:
                record.planning_status = "planned"

    @api.model
    def _search_planning_status(self, operator, value):
        if operator not in ("=", "!="):
            raise NotImplementedError(
                "Planning Status supports only '=' and '!=' searches."
            )
        today = fields.Date.context_today(self)
        due_soon_limit = today + timedelta(days=30)
        domains = {
            "overdue": [
                ("status", "=", "scheduled"),
                ("maintenance_date", "<", today),
            ],
            "due_soon": [
                ("status", "=", "scheduled"),
                ("maintenance_date", ">=", today),
                ("maintenance_date", "<=", due_soon_limit),
            ],
            "planned": [
                ("status", "=", "scheduled"),
                ("maintenance_date", ">", due_soon_limit),
            ],
            "not_scheduled": [
                ("status", "!=", "scheduled"),
            ],
        }
        domain = domains.get(value, [("id", "=", 0)])
        if operator == "=":
            return domain
        return ["!"] + domain

    def action_start_maintenance(self):
        self.write({
            "status": "in_progress",
        })

    def action_complete_maintenance(self):
        self.write({
            "status": "completed",
        })

    def action_cancel_maintenance(self):
        self.write({
            "status": "cancelled",
        })