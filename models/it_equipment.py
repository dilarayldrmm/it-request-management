from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ITEquipment(models.Model):
    _name = "it.equipment"
    _description = "IT Equipment"
    _order = "name"

    _sql_constraints = [
        (
            "serial_number_unique",
            "unique(serial_number)",
            "Serial number must be unique.",
        ),
    ]



    name = fields.Char(
        string="Equipment Name",
        required=True,
    )

    serial_number = fields.Char(
        string="Serial Number",
        required=True,
        copy=False,
    )

    equipment_type = fields.Selection(
        [
            ("laptop", "Laptop"),
            ("desktop", "Desktop"),
            ("monitor", "Monitor"),
            ("printer", "Printer"),
            ("phone", "Phone"),
            ("network", "Network Device"),
            ("other", "Other"),
        ],
        string="Equipment Type",
        required=True,
        default="laptop",
    )

    assigned_to_id = fields.Many2one(
        "res.users",
        string="Assigned To",
    )

    status = fields.Selection(
        [
            ("available", "Available"),
            ("assigned", "Assigned"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ],
        string="Status",
        required=True,
        default="available",
    )

    purchase_date = fields.Date(
        string="Purchase Date",
    )

    warranty_end_date = fields.Date(
        string="Warranty End Date",
    )

    warranty_status = fields.Selection(
        [
            ("under_warranty", "Under Warranty"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
            ("no_warranty", "No Warranty"),
        ],
        string="Warranty Status",
        compute="_compute_warranty_info",
        search="_search_warranty_status",
    )

    warranty_days_left = fields.Integer(
        string="Warranty Days Left",
        compute="_compute_warranty_info",
    )

    note = fields.Text(
        string="Notes",
    )

    active = fields.Boolean(
        default=True,
    )

    # ---------------------------------------------------------
    # REQUEST RELATION
    # ---------------------------------------------------------

    request_ids = fields.One2many(
        "it.request",
        "equipment_id",
        string="IT Requests",
    )

    request_count = fields.Integer(
        string="Request Count",
        compute="_compute_request_count",
    )

    @api.depends("request_ids")
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.request_ids)

    # ---------------------------------------------------------
    # MAINTENANCE RELATION
    # ---------------------------------------------------------

    maintenance_ids = fields.One2many(
        "it.equipment.maintenance",
        "equipment_id",
        string="Maintenances",
    )

    maintenance_count = fields.Integer(
        string="Maintenance Count",
        compute="_compute_maintenance_count",
    )

    next_maintenance_date = fields.Date(
        string="Next Planned Maintenance",
        compute="_compute_next_maintenance_info",
    )

    maintenance_plan_status = fields.Selection(
        [
            ("no_schedule", "No Planned Maintenance"),
            ("overdue", "Overdue"),
            ("due_soon", "Due Soon"),
            ("planned", "Planned"),
        ],
        string="Maintenance Plan Status",
        compute="_compute_next_maintenance_info",
    )

    @api.depends("maintenance_ids")
    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = len(
                record.maintenance_ids
            )

    @api.depends(
        "maintenance_ids.status",
        "maintenance_ids.maintenance_date",
    )
    def _compute_next_maintenance_info(self):
        today = fields.Date.context_today(self)
        due_soon_limit = today + timedelta(days=30)

        for record in self:
            scheduled_maintenances = record.maintenance_ids.filtered(
                lambda maintenance: (
                    maintenance.status == "scheduled"
                    and maintenance.maintenance_date
                )
            )

            if not scheduled_maintenances:
                record.next_maintenance_date = False
                record.maintenance_plan_status = "no_schedule"
                continue

            next_date = min(
                scheduled_maintenances.mapped(
                    "maintenance_date"
                )
            )
            record.next_maintenance_date = next_date

            if next_date < today:
                record.maintenance_plan_status = "overdue"
            elif next_date <= due_soon_limit:
                record.maintenance_plan_status = "due_soon"
            else:
                record.maintenance_plan_status = "planned"

    # ---------------------------------------------------------
    # ASSIGNMENT HISTORY
    # ---------------------------------------------------------

    assignment_ids = fields.One2many(
        "it.equipment.assignment",
        "equipment_id",
        string="Assignment History",
    )

    assignment_count = fields.Integer(
        string="Assignment Count",
        compute="_compute_assignment_count",
    )

    @api.depends("assignment_ids")
    def _compute_assignment_count(self):
        for record in self:
            record.assignment_count = len(
                record.assignment_ids
            )

    @api.depends("warranty_end_date")
    def _compute_warranty_info(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.warranty_end_date:
                record.warranty_status = "no_warranty"
                record.warranty_days_left = 0
                continue

            days_left = (
                record.warranty_end_date - today
            ).days
            record.warranty_days_left = days_left

            if days_left < 0:
                record.warranty_status = "expired"
            elif days_left <= 30:
                record.warranty_status = "expiring_soon"
            else:
                record.warranty_status = "under_warranty"

    @api.model
    def _search_warranty_status(self, operator, value):
        if operator != "=":
            raise NotImplementedError(
                "Warranty status currently supports '=' searches only."
            )

        today = fields.Date.context_today(self)
        thirty_days_later = today + relativedelta(days=30)

        if value == "no_warranty":
            return [("warranty_end_date", "=", False)]
        if value == "expired":
            return [("warranty_end_date", "<", today)]
        if value == "expiring_soon":
            return [
                ("warranty_end_date", ">=", today),
                ("warranty_end_date", "<=", thirty_days_later),
            ]
        if value == "under_warranty":
            return [("warranty_end_date", ">", thirty_days_later)]
        return []

   

    def _close_active_assignment(self):
        self.ensure_one()

        active_assignments = self.env[
            "it.equipment.assignment"
        ].sudo().search(
            [
                ("equipment_id", "=", self.id),
                ("status", "=", "active"),
            ]
        )
                                   #Eski kullanıcının kaydını silmiyorum; Returned yapıp dönüş tarihini kaydediyorum
        if active_assignments:
            active_assignments.write(
                {
                    "status": "returned",
                    "returned_date": fields.Datetime.now(),
                }
            )

    def _create_assignment_history(self, user_id):
        self.ensure_one()

        if not user_id:
            return

        self.env[
            "it.equipment.assignment"
        ].sudo().create(
            {
                "equipment_id": self.id,
                "user_id": user_id,
                "assigned_date": fields.Datetime.now(),
                "status": "active",
            }
        )

   

    @api.onchange("assigned_to_id")
    def _onchange_assigned_to_id(self):
        for record in self:

            if record.status == "retired":
                continue

            has_active_maintenance = any(
                maintenance.status == "in_progress"
                for maintenance in record.maintenance_ids
            )

            if has_active_maintenance:
                record.status = "maintenance"

            elif record.assigned_to_id:
                record.status = "assigned"

            elif record.status == "assigned":
                record.status = "available"

   
    # Create
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            if vals.get("assigned_to_id"):
                vals["status"] = "assigned"

        records = super().create(vals_list)

        for record in records:
            if record.assigned_to_id:
                record._create_assignment_history(
                    record.assigned_to_id.id
                )

        return records

   
    
    

    def write(self, vals):

        # Normal field update:
        # no assignment change means no history operation.
        if "assigned_to_id" not in vals:
            return super().write(vals)

        new_user_id = vals.get("assigned_to_id") or False

        for record in self:

            old_user_id = (
                record.assigned_to_id.id
                if record.assigned_to_id
                else False
            )

            record_vals = vals.copy()

            # Keep retired equipment retired.
            if record.status != "retired":

                has_active_maintenance = any(
                    maintenance.status == "in_progress"
                    for maintenance in record.maintenance_ids
                )

                if has_active_maintenance:
                    record_vals["status"] = "maintenance"

                elif new_user_id:
                    record_vals["status"] = "assigned"

                else:
                    record_vals["status"] = "available"

            result = super(
                ITEquipment,
                record,
            ).write(record_vals)

                                                                       #önemli 
            if old_user_id != new_user_id:

                record._close_active_assignment()

                if new_user_id:
                    record._create_assignment_history(
                        new_user_id
                    )

            if not result:
                return result

        return True

   
    def action_view_requests(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": f"Requests - {self.name}",
            "res_model": "it.request",
            "view_mode": "kanban,list,form",
            "domain": [
                ("equipment_id", "=", self.id),
            ],
            "context": {
                "default_equipment_id": self.id,
            },
            "target": "current",
        }

   

    def action_view_maintenances(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": f"Maintenances - {self.name}",
            "res_model": "it.equipment.maintenance",
            "view_mode": "list,form",
            "domain": [
                ("equipment_id", "=", self.id),
            ],
            "context": {
                "default_equipment_id": self.id,
            },
            "target": "current",
        }

   

    def action_view_assignments(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": f"Assignment History - {self.name}",
            "res_model": "it.equipment.assignment",
            "view_mode": "list,form",
            "domain": [
                ("equipment_id", "=", self.id),
            ],
            "context": {
                "default_equipment_id": self.id,
            },
            "target": "current",
        }