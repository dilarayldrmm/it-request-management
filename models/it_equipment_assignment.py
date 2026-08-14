from odoo import fields, models


class ITEquipmentAssignment(models.Model):
    _name = "it.equipment.assignment"
    _description = "IT Equipment Assignment History"
    _order = "assigned_date desc, id desc"

    equipment_id = fields.Many2one(
        "it.equipment",
        string="Equipment",
        required=True,
        ondelete="cascade",
    )

    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        required=True,
    )

    assigned_date = fields.Datetime(
        string="Assigned Date",
        required=True,
        default=fields.Datetime.now,
    )

    returned_date = fields.Datetime(
        string="Returned Date",
        readonly=True,
    )

    status = fields.Selection(
        [
            ("active", "Active"),
            ("returned", "Returned"),
        ],
        string="Status",
        required=True,
        default="active",
    )

    note = fields.Text(
        string="Notes",
    )