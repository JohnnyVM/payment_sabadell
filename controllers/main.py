# -*- coding: utf-8 -*-

import urllib.parse
import binascii
import logging

from hashlib import sha256, md5
from decimal import Decimal

import werkzeug
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class SabadellController(http.Controller):

    def _get_website_url(self):
        domain = request.httprequest.host
        if domain and domain != "localhost":
            base_url = "{}://{}".format(
                request.httprequest.environ["wsgi.url_scheme"],
                request.httprequest.host
            )
        else:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url or ""

    @http.route('/sabadell_payment', auth='public', method=["GET"], csrf=False, website=True)
    def payment(self, **post):
        url = "https://api.paycomet.com/gateway/ifr-bankstore"

        provider = request.env['payment.acquirer'].sudo().search(
                [('provider', '=', 'sabadell'), '|', ('website_id', '=', request.website.id), ('website_id', '=', False)]
        )
        provider.ensure_one()

        if provider.sabadell_integration == 'fullscreen':
            params = {
                "MERCHANT_MERCHANTCODE": provider.sudo().sabadell_merchant_merchantcode,
                "MERCHANT_TERMINAL": str(provider.sudo().sabadell_merchant_terminal),
                "OPERATION": "1",
                "MERCHANT_ORDER": post.get("reference"),
                "MERCHANT_AMOUNT": str(int(Decimal(post.get("amount")) * 100)),
                "3DSECURE": str(int(provider.sudo().sabadell_3dsecure)),
            }

            list_languages = provider.sudo()._fields['sabadell_language'].get_values(request.env)
            partner_lang = post.get("partner_lang")
            if partner_lang.split("_")[0].lower() in list_languages:
                params["LANGUAGE"] = partner_lang.split("_")[0].lower()
            else:
                params["LANGUAGE"] = provider.sudo().sabadell_language

            currency = request.env['res.currency'].browse(int(post.get("currency_id")))
            if currency.name not in provider.sudo()._fields['sabadell_currency'].get_values(request.env):
                _logger.info("%s invalid currency for transaction", currency.name)
                return werkzeug.utils.redirect(post.get("return_url", "/payment/process"))

            params["MERCHANT_CURRENCY"] = currency.name

            # https://www.bsdev.es/en/documentacion/psd2-parametros
            # LWV | Exception for low amounts. This exception includes payments of 30 EUR or less 
            # TODO ??? abrir un ticket para saber que significa esto
            # if int(params["MERCHANT_AMOUNT"]) <= 3000:
            #     params["MERCHANT_SCA_EXCEPTION"] = "LWV"

            # THESE are landing endpoint. can be override in each call then is not necesary a configuration.
            # for historic compatibility URLOK receive enought parameters to be used as check payment
            # but the info message will arrive to the notification endpoint, i will not use the compatibility path
            # and i will simple redirect to order list for ok and error for ko
            params["URLOK"] = self._get_website_url() + '/sabadell/ok'
            params["URLKO"] = self._get_website_url() + '/sabadell/ko'

            # params["MERCHANT_DATA"] not seem necesary give to the bank the data of the clients

            params["MERCHANT_MERCHANTSIGNATURE"] = \
                    sha256(bytes(
                        params["MERCHANT_MERCHANTCODE"] +
                        params["MERCHANT_TERMINAL"] +
                        params["OPERATION"] +
                        params["MERCHANT_ORDER"] +
                        params["MERCHANT_AMOUNT"] +
                        params["MERCHANT_CURRENCY"] +
                        md5(bytes(provider.sudo().sabadell_merchant_password, 'utf-8')).hexdigest(),
                        'utf-8'
                    )).hexdigest()

            iframe_url = url + '?' + urllib.parse.urlencode(params)

            return http.request.render("payment_sabadell.sabadell_iframe", {"iframe_url": iframe_url})

        raise NotImplementedError("This integration is not implemented")

    @http.route('/sabadell/ok', type="http", auth="public", method=["GET"], csrf=False, sitemap=False)
    def transaction_ok(self, **post):
        # https://github.com/odoo/odoo/blob/a4d81bf754c154216c24756e19908904954f4305/addons/payment/controllers/portal.py#L43
        # Get the current payment transaction from the environment
        tx_ids_list = request.session.get("__payment_tx_ids__", [])
        payment_transaction_ids = request.env['payment.transaction'].sudo().browse(tx_ids_list).exists()

        # https://github.com/odoo/odoo/blob/13.0/addons/payment/models/payment_acquirer.py#L760
        # Mark this transactions as aproved
        payment_transaction_ids._set_transaction_authorized()

        return werkzeug.utils.redirect("/payment/process")

    @http.route('/sabadell/ko', type="http", auth="public", method=["GET"], csrf=False, sitemap=False)
    def transaction_ko(self, **post):
        return werkzeug.utils.redirect("/payment/process")

    # TODO look how initialize the endpoints in runtime wheni the config notification field change
    @http.route('/sabadell/<endpoint>', type="http", auth="public", method=["POST"], csrf=False, sitemap=False, website=True)
    def transaction_notification(self, endpoint, **post):
        _logger.info("Notification arrive to %s, params: %s", endpoint, post)
        provider = request.env['payment.acquirer'].sudo().search(
                [('provider', '=', 'sabadell'), '|', ('website_id', '=', request.website.id), ('website_id', '=', False)]
        )
        provider.ensure_one()

        if endpoint == provider.sudo().sabadell_payment_notification:
            request.env['payment.transaction'].sudo().sabadell_form_feedback(post, 'sabadell')
