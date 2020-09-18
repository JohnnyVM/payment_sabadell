# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from . import models
from . import controllers

from odoo.addons.payment import reset_payment_provider

def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'sabadell')
