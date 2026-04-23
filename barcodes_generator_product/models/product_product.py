# Copyright (C) 2014-Today GRAP (http://www.grap.coop)
# Copyright (C) 2016-Today La Louve (http://www.lalouve.net)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "barcode.generate.mixin"]

    # Neutraliza la restricción SQL del core para permitir barcodes vacíos (False)
    # La unicidad se valida por Python ignorando valores False
    _sql_constraints = [
        ("barcode_uniq", "CHECK(1=1)", ""),
    ]

    @api.model
    def create(self, vals):
        if "barcode" in vals:
            barcode_val = vals["barcode"]
            if barcode_val is None or (
                isinstance(barcode_val, str) and not barcode_val.strip()
            ):
                vals["barcode"] = False
        return super().create(vals)

    def write(self, vals):
        if isinstance(vals.get("barcode"), str) and not vals["barcode"].strip():
            vals["barcode"] = False
        return super().write(vals)

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
