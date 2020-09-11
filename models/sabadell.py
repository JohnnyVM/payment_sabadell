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

    sabadell_email_account = \
            fields.Char("Sabadell email account", required_if_provider="sabadell", groups="base.group_user")

    # Payment types
    sabadell_integration = fields.Selection(
        [('fullscreen', 'Fullscreen'), ('iframe', 'Iframe'), ('embedded', 'Embedded')],
        "Sabadell integration method",
        default="fullscreen",
        required=True,
        required_if_provider="sabadell",
        help="Integration method: https://www.bsdev.es/en/documentacion/introduccion"
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
