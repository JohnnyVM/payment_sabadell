# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
    Minimun implementation for Sabadell payment
"""

import logging

from decimal import Decimal

from odoo import models, fields, http

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
            fields.Char("Payment ok url", help="HOST/sabadell/<field>", groups="base.group_user")

    sabadell_payment_ko = \
            fields.Char("Payment ko url", help="HOST/sabadell/<field>", groups="base.group_user")

    sabadell_payment_notification = \
            fields.Char("Payment notification url", help="HOST/sabadell/<field>", groups="base.group_user")

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
    """ The documentation of Payment class is wrong, see form_feedback for more info """
    _inherit="payment.transaction"

    def _sabadell_form_get_tx_from_data(self, data):
        """ Given a data dict coming from sabadell, verify it and find the related transaction record.
            Received:
                'r': reference,
                'ret':
                'i': amount
                'h':
        """
        tx = self.search([('reference', '=', data.get('r'))])
        tx.ensure_one()
        return tx

    def _sabadell_form_get_invalid_parameters(self, data):
        """ TODO """
        return dict()

    def _sabadell_form_validate(self, data):
        """ Last check """
        state = ["done", "pending", "cancel", "error"][0]
        vals = {
            'state': state,
            'date': fields.Datetime.now()
        }
        self.write(vals)
        return state != "error"


    def sabadell_form_feedback(self, data, acquirer_name):
        """ 1 - form_data valida los datos recibidos y aprueba el pago
            2 - Actualizamos la información de la venta
        """
        res = super(SabadellTransaction, self).form_feedback(data, acquirer_name)
        if res:
            tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
            tx = getattr(self, tx_find_method_name)(data)

            amount_match = str(int(Decimal(tx.amount) * 100)) == data.get('i')
            if amount_match:
                if tx.state == 'done':
                    _logger.info('<%s> transaction completed, confirming order %s (ID %s)', acquirer_name, tx.sale_order_ids.name, tx.sale_order_ids.id)
                    tx.sale_order_ids.with_context(send_email=True).action_confirm()

                elif (tx.state != 'cancel' and tx.sale_order_ids.state == 'draft'):
                    _logger.info('<%s> transaction pending, sending quote email for order %s (ID %s)',acquirer_name, tx.sale_order_ids.name, tx.sale_order_ids.id)
                    tx.sale_order_ids.force_quotation_send()

            else:
                _logger.warning('<%s> transaction MISMATCH for order %s (ID %s)', acquirer_name, tx.sale_order_ids.name, tx.sale_order_ids.id)

