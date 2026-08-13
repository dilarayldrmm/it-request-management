{
    "name": "IT Request Management",
    "version": "18.0.1.0.0",
    "summary": "Internal IT request and equipment management",
    "description": """
        Manage internal IT support requests, categories,
        equipment and request workflows.
    """,
    "author": "Dilara",
    "category": "Services/IT Services",
    "license": "LGPL-3",

    "depends": [
        "base",
        "mail",
        #şu anlama geliyor: bizim modülümüz Odoo’nun temel modellerine ve altyapısına bağımlı. İleride mail.thread kullanınca buraya mail, çalışan modeli kullanmaya karar verirsek hr gibi bağımlılıklar ekleyebiliriz.
    ],

    "data": [
    "security/it_request_security.xml",
    "security/ir.model.access.csv",
    "data/it_request_sequence.xml",
    "data/it_request_activity_type.xml",
    "views/it_request_views.xml",
    "views/it_request_report_views.xml",
    "views/it_request_dashboard_views.xml",
    "views/it_request_category_views.xml",
    ],

    "installable": True,
    "application": True,
}