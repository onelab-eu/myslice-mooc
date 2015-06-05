'''
    MyOps2 - a new monitoring system for PlanetLab and other testbeds
    
    (c) 2014 - 2015 Ciro Scognamiglio <ciro.scognamiglio@lip6.fr>
'''

import ipwhois

def lookup(ip):
    '''
    {'asn': '2200',
     'asn_cidr': '2001:660::/32',
     'asn_country_code': 'FR',
     'asn_date': '2000-03-21',
     'asn_registry': 'ripencc',
     'nets': [{'abuse_emails': None,
               'address': 'GIP RENATER\n23-25 Rue Daviel\n75013 PARIS\nFRANCE',
               'cidr': '2001:660:3302::/48',
               'city': None,
               'country': 'FR',
               'created': None,
               'description': 'Universite Pierre et Marie CURIE',
               'handle': 'BT261-RIPE',
               'misc_emails': None,
               'name': 'FR-U-PARIS6-RAP-10',
               'postal_code': None,
               'range': '2001:660:3302::/48',
               'state': None,
               'tech_emails': None,
               'updated': None}],
     'query': '2001:660:3302:2826:79fe:b444:7813:e97e',
     'raw': None,
     'raw_referral': None,
     'referral': None}
    '''
    return ipwhois.IPWhois(ip).lookup()