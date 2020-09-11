# -*- coding: utf-8 -*-
from odoo import http

class SabadellController(http.Controller):

    @http.route('/sabadell_payment', auth='public', csrf=False)
    def main(self, **kwargs):
        return http.request.render("payment_sabadell.sabadell_iframe")
