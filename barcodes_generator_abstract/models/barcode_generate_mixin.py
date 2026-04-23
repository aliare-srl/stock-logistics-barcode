# Copyright (C) 2014-TODAY GRAP (http://www.grap.coop)
# Copyright (C) 2016-TODAY La Louve (http://www.lalouve.net)
# Copyright 2017 LasLabs Inc.
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

import barcode  # pylint: disable=W7936

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class BarcodeGenerateMixin(models.AbstractModel):
    _name = "barcode.generate.mixin"
    _description = "Generate Barcode Mixin"

    # Column Section
    barcode_rule_id = fields.Many2one(
        string="Barcode Rule", comodel_name="barcode.rule"
    )

    barcode_base = fields.Integer(copy=False)

    generate_type = fields.Selection(
        related="barcode_rule_id.generate_type",
    )

    @api.model
    def create(self, vals):
        if isinstance(vals.get("barcode"), str) and not vals["barcode"].strip():
            vals["barcode"] = False
        return super().create(vals)

    def write(self, vals):
        if isinstance(vals.get("barcode"), str) and not vals["barcode"].strip():
            vals["barcode"] = False
        return super().write(vals)

    # View Section
    def generate_base(self):
        for item in self:
            if item.generate_type != "sequence":
                raise exceptions.UserError(
                    _(
                        "Generate Base can be used only with barcode rule with"
                        " 'Generate Type' set to 'Base managed by Sequence'"
                    )
                )
            if not item.barcode_rule_id.sequence_id:
                raise exceptions.UserError(
                    _("The barcode rule '%s' has no sequence configured.")
                    % item.barcode_rule_id.name
                )
            item.barcode_base = int(item.barcode_rule_id.sequence_id.next_by_id())

    def generate_barcode(self):
        for item in self:
            if not item.barcode_rule_id:
                continue
            custom_code_template = self._get_custom_barcode(item)
            if not custom_code_template:
                continue
            padding = item.barcode_rule_id.padding
            barcode_class = barcode.get_barcode_class(item.barcode_rule_id.encoding)

            _MAX_RETRIES = 10
            for attempt in range(_MAX_RETRIES):
                str_base = str(item.barcode_base).rjust(padding, "0")
                candidate = custom_code_template.replace("." * padding, str_base)
                generated = str(barcode_class(candidate))

                duplicate = self.search(
                    [("barcode", "=", generated), ("id", "!=", item.id)],
                    limit=1,
                )
                if not duplicate:
                    item.barcode = generated
                    break

                _logger.warning(
                    "Barcode %s already in use (base=%s, attempt=%d/%d),"
                    " advancing sequence for '%s'.",
                    generated,
                    item.barcode_base,
                    attempt + 1,
                    _MAX_RETRIES,
                    item.display_name,
                )
                if not item.barcode_rule_id.sequence_id:
                    raise exceptions.UserError(
                        _(
                            "Cannot generate a unique barcode: the rule '%s'"
                            " has no sequence configured."
                        )
                        % item.barcode_rule_id.name
                    )
                item.barcode_base = int(
                    item.barcode_rule_id.sequence_id.next_by_id()
                )
            else:
                raise exceptions.UserError(
                    _(
                        "Could not generate a unique barcode for '%s' after"
                        " %d attempts. Please check the sequence configuration."
                    )
                    % (item.display_name, _MAX_RETRIES)
                )

    # Custom Section
    @api.model
    def _get_custom_barcode(self, item):
        """
        If the pattern is '23.....{NNNDD}'
        this function will return '23.....00000'
        Note : Overload _get_replacement_char to have another char
        instead that replace 'N' and 'D' char.
        """
        if not item.barcode_rule_id:
            return False

        # Define barcode
        custom_code = item.barcode_rule_id.pattern
        custom_code = custom_code.replace("{", "").replace("}", "")
        custom_code = custom_code.replace("D", self._get_replacement_char("D"))
        return custom_code.replace("N", self._get_replacement_char("N"))

    @api.model
    def _get_replacement_char(self, char):
        """
        Can be overload by inheritance
        Define wich character will be used instead of the 'N' or the 'D'
        char, present in the pattern of the barcode_rule_id
        """
        return "0"
