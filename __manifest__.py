{
    "name": "Payment adquirer for bank Sabadell",
    "summary": "Payment Acquirer: Sabadell Implementation",
    "version": "0.1.0",
    "author": "Juan Vázquez Moreno <vmjuan90@gmail.com>",
    "website": "https://guadalstore.es",
    "category": "Payment Acquirer",
    "depends": ["website", "payment"],
    "data": [
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml'
        ],
    "license": "AGPL-3",
    "installable": True,
    'uninstall_hook': 'uninstall_hook'
}
