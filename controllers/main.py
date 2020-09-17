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

    @http.route('/sabadell_payment', auth='public', csrf=False, cors='*')
    def payment(self, **post):
        url = "https://api.paycomet.com/gateway/ifr-bankstore"

        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'sabadell')])
        provider.ensure_one()

        params = {
            "MERCHANT_MERCHANTCODE": provider.sabadell_merchant_merchantcode,
            "MERCHANT_TERMINAL": str(provider.sabadell_merchant_terminal),
            "OPERATION": "1",
            "MERCHANT_ORDER": post.get("reference"),
            "MERCHANT_AMOUNT": str(int(Decimal(post.get("amount")) * 100)),
            "MERCHANT_CURRENCY": provider.sabadell_currency,
            "3DSECURE": str(int(provider.sabadell_3dsecure)),
        }

        list_languages = provider._fields['sabadell_language'].get_values(request.env)
        partner_lang = post.get("partner_lang")
        if partner_lang.split("_")[0].lower() in list_languages:
            params["LANGUAGE"] = partner_lang.split("_")[0].lower()
        else:
            params["LANGUAGE"] = provider.sabadell_language

        if int(params["MERCHANT_AMOUNT"]) <= 30000:
            params["MERCHANT_SCA_EXCEPTION"] = "LWV"

        # params["MERCHANT_DATA"]
        # params Curency

        params["MERCHANT_MERCHANTSIGNATURE"] = \
                sha256(bytes(
                    params["MERCHANT_MERCHANTCODE"] +
                    params["MERCHANT_TERMINAL"] +
                    params["OPERATION"] +
                    params["MERCHANT_ORDER"] +
                    params["MERCHANT_AMOUNT"] +
                    params["MERCHANT_CURRENCY"] +
                    md5(bytes(provider.sabadell_merchant_password, 'utf-8')).hexdigest(),
                    'utf-8'
                )).hexdigest()

        # build URL
        payload = urllib.parse.urlencode(params)
        iframe_url = url + '?' + payload

        return http.request.render("payment_sabadell.sabadell_iframe", {"iframe_url": iframe_url})

    @http.route('/sabadell_ko', website=False, type="http", multilang=False, lang=None)
    def transaction_ko(self, **post):
        _logger.info("Sabadell KO transaction feedback {}".format(post))        
        return "Some error happens requesting the payment, payment canceled..."

    @http.route('/sabadell_notification', type="http", auth="public", method=["GET"], website=True, csrf=False)
    def transaction_notification(self, **post):
        _logger.info("Sabadell notification transaction feedback {}".format(post)) 
        return werkzeug.utils.redirect(post.get("return_url", "/payment/process"))

    @http.route('/sabadell_ok', type="http", auth="public", method=["GET"], website=True, lang=None, multilang=False)
    def transaction_ok(self, **post):
        _logger.info("Sabadell OK transaction feedback {}".format(post)) 
        request.env['payment.transaction'].sudo().form_feedback(post, 'sabadell')
        return werkzeug.utils.redirect(post.get("return_url", "/payment/process"))


