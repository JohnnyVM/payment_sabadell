# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
    Minimun implementation for Sabadell payment
"""

import logging

from odoo import api, models, fields, http

_logger = logging.getLogger(__name__)

class AcquirerSabadell(models.Model):
    """ Sabadell Model class """
    _inherit = 'payment.acquirer'

    cription = "Sabadell payment acquirer model"

    provider = fields.Selection(selection_add=[('sabadell', 'Sabadell')])

    sabadell_merchant_merchantcode = \
            fields.Char("Merchant code", size=8, required_if_provider="sabadell", groups="base.group_user")

    sabadell_merchant_terminal = \
            fields.Integer("Merchant terminal", required_if_provider="sabadell", groups="base.group_user")

    sabadell_merchant_password = \
            fields.Char("Merchant password", required_if_provider="sabadell", groups="base.group_user")

    sabadell_payment_ok = \
            fields.Char("Payment ok url", groups="base.group_user")

    sabadell_payment_ko = \
            fields.Char("Payment ko url", groups="base.group_user")

    sabadell_language = fields.Selection(
        [('es', 'Español'), ('en', 'English'), ('fr', 'French'), ('de', 'German'), ('it', 'Italian')],
        "Sabadell language environment",
        default="en",
        required_if_provider="sabadell"
    )

    sabadell_currency = fields.Selection(
        [('EUR', 'Euro'), ('USD', 'American dollar'), ('GBP', 'Libra esterlina'), ('JPY', 'Japanese yen')],
        "Transaction currency",
        default="EUR",
        required_if_provider="sabadell"
    )

    sabadell_3dsecure = fields.Boolean("3DSecure", groups="base.group_user")

    # Payment types
    sabadell_integration = fields.Selection(
        [('fullscreen', 'Fullscreen'), ('iframe', 'Iframe'), ('embedded', 'Embedded')],
        "Sabadell integration method",
        default="fullscreen",
        required_if_provider="sabadell",
        help="Integration method: https://www.bsdev.es/en/documentacion/introduccion",
        groups="base.group_user"
    )

    @api.model
    def _get_website_url(self):
        domain = http.request.website.domain
        if domain and domain != "localhost":
            base_url = "{}://{}".format(
                http.request.httprequest.environ["wsgi.url_scheme"],
                http.request.website.domain,
            )
        else:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url or ""

    def sabadell_get_form_action_url(self):
        """ Return URL for payment controller"""
        return self._get_website_url() + "/sabadell_payment"

#    @api.multi
#    def sabadell_form_generate_values(self, values):
#        self.ensure_one()
#        return dict() # values added to button "Pay Now" render response

#    def compute fees(self):
#       pass


class SabadellTransaction(models.Model):
    _inherit="payment.transaction"

    def sabadell_form_feedback(self, data):
        _logger.info("sabadell_form_feedback data: {}".format(data))
