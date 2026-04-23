# Copyright (C) 2014-Today GRAP (http://www.grap.coop)
# Copyright (C) 2016-Today La Louve (http://www.lalouve.net)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Neutraliza la restricción SQL del core para permitir barcodes vacíos (False)
    # La unicidad se valida por Python ignorando valores False
    _sql_constraints = [
        ("barcode_uniq", "CHECK(1=1)", ""),
    ]

    # Related to display product product information if is_product_variant
    barcode_rule_id = fields.Many2one(
        related="product_variant_ids.barcode_rule_id",
        string="Barcode Rule",
        readonly=False,
        comodel_name="barcode.rule",
    )

    barcode_base = fields.Integer(
        related="product_variant_ids.barcode_base",
        readonly=False,
        string="Barcode Base",
    )

    generate_type = fields.Selection(
        string="Generate Type",
        readonly=True,
        related="product_variant_ids.barcode_rule_id.generate_type",
    )

    # View Section
    def generate_base(self):
        self.product_variant_ids.generate_base()

    def generate_barcode(self):
        self.ensure_one()
        self.product_variant_ids.generate_barcode()

    @api.onchange("barcode_rule_id")
    def onchange_barcode_rule_id(self):
        self.generate_type = self.barcode_rule_id.generate_type

    @api.constrains("barcode")
    def _check_barcode_uniqueness(self):
        for record in self:
            if not record.barcode:
                continue
            duplicate = self.search(
                [("barcode", "=", record.barcode), ("id", "!=", record.id)],
                limit=1,
            )
            if duplicate:
                raise exceptions.ValidationError(
                    _(
                        'El código de barras "%s" ya está asignado al producto "%s".'
                    )
                    % (record.barcode, duplicate.display_name)
                )

    # Overload Section
    @api.model
    def create(self, vals):
        if "barcode" in vals:
            barcode_val = vals["barcode"]
            if barcode_val is None or (
                isinstance(barcode_val, str) and not barcode_val.strip()
            ):
                vals["barcode"] = False
        template = super().create(vals)

        # this is needed to set given values to first variant after creation
        # these fields should be moved to product as lead to confusion
        # (Ref. product module feature in Odoo Core)
        related_vals = {}
        for field in ["barcode_rule_id", "barcode_base"]:
            if vals.get(field, False):
                related_vals[field] = vals[field]
        if related_vals:
            template.write(related_vals)
        return template

    def write(self, vals):
        if "barcode" in vals:
            barcode_val = vals["barcode"]
            if barcode_val is None or (
                isinstance(barcode_val, str) and not barcode_val.strip()
            ):
                vals["barcode"] = False
        return super().write(vals)
