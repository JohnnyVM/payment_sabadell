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
                request.httprequest.host,
            )
        else:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url or ""

    @http.route('/sabadell_payment', auth='public', csrf=False, sitemap=False)
    def payment(self, **post):
        url = "https://api.paycomet.com/gateway/ifr-bankstore"

        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'sabadell')])
        provider.ensure_one()

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


        if int(params["MERCHANT_AMOUNT"]) <= 30000:
            params["MERCHANT_SCA_EXCEPTION"] = "LWV"

        if provider.sudo().sabadell_payment_ko:
            params["URLKO"] = self._get_website_url() + provider.sudo().sabadell_payment_ko

        if provider.sudo().sabadell_payment_ko:
            params["URLOK"] = self._get_website_url() + provider.sudo().sabadell_payment_ok

        # params["MERCHANT_DATA"]

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

        # build URL
        payload = urllib.parse.urlencode(params)
        iframe_url = url + '?' + payload

        return http.request.render("payment_sabadell.sabadell_iframe", {"iframe_url": iframe_url})

    @http.route('/sabadell/<endpoint>', type="http", auth="public", website=True, csrf=False, sitemap=False)
    def transaction_notification(self, endpoint, **post):
        """ TODO look for how initialize the endpoints """
        _logger.info("Sabadell arrive to %s, params: %s", endpoint, post)
        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'sabadell')])
        provider.ensure_one()

        if '/sabadell/' + endpoint == provider.sudo().sabadell_payment_ok:
            request.env['payment.transaction'].sudo().sabadell_form_feedback(post, 'sabadell')
            return werkzeug.utils.redirect(post.get("return_url", "/payment/process"))

        if '/sabadell/' + endpoint == provider.sudo().sabadell_payment_ko:
            pass

        if '/sabadell/' + endpoint == provider.sudo().sabadell_payment_notification:
            pass

        return werkzeug.utils.redirect(post.get("return_url", "/payment/process"))
