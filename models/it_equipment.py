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

    note = fields.Text(
        string="Notes",
    )

    active = fields.Boolean(
        default=True,
    )

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

    @api.onchange("assigned_to_id")
    def _onchange_assigned_to_id(self):
        for record in self:
            if record.assigned_to_id:
                record.status = "assigned"
            elif record.status == "assigned":
                record.status = "available"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("assigned_to_id"):
                vals["status"] = "assigned"

        return super().create(vals_list)

    def write(self, vals):
        vals = vals.copy()

        if "assigned_to_id" in vals:
            if vals["assigned_to_id"]:
                vals["status"] = "assigned"
            else:
                for record in self:
                    record_vals = vals.copy()

                    if record.status == "assigned":
                        record_vals["status"] = "available"

                    super(
                        ITEquipment,
                        record,
                    ).write(record_vals)

                return True

        return super().write(vals)

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