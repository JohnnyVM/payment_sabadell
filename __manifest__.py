{
    "name": "Payment adquirer for bank Sabadell",
    "summary": "Payment Acquirer: Sabadell/Paycomet fullscreen/GET Implementation",
    "version": "13.0.1.0",
    "author": "Juan Vázquez Moreno <vmjuan90@gmail.com>",
    "website": "",
    "category": "Payment Acquirer",
    "depends": ["website_sale", "payment"],
    "data": [
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml'
        ],
    "license": "AGPL-3",
    "installable": True,
    'uninstall_hook': 'uninstall_hook'
}
