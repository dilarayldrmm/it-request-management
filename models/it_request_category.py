from odoo import models, fields


class ITRequestCategory(models.Model):
    _name = "it.request.category"
    _description = "IT Request Category"

    name = fields.Char(
        string="Category Name",
        required=True,
    )

    description = fields.Text(
        string="Description",
    )

    active = fields.Boolean(
        default=True,
    )