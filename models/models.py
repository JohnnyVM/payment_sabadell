# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class AcquirerSabadell(models.Model):
    _inherit = 'payment.acquirer'

    _description = "Sabadell payment adquirer model"

    provider = fields.Selection(selection_add=[('sabadell', 'Sabadell')])
