# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class AcquirerSabadell(models.Model):
    _inherit = 'payment.acquirer'

    cription = "Sabadell payment acquirer model"

    provider = fields.Selection(selection_add=[('sabadell', 'Sabadell')])

    sabadell_email_account = \
            fields.Char("Sabadell email account", required_if_provider="sabadell", groups="base.group_user")

    def sabadell_get_form_action_url(self):
        return "sabadell_get_form_action_url"

    @api.multi 
    def sabadell_form_generate_values(self, reference, amount, currency,
            partner_id=False, partner_values=None, tx_custom_values=None):
        self.ensure_one()


    # TODO compute fees
    
