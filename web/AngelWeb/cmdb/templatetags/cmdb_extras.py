from django import template
from django.conf import settings
from cmdb.models import *
import datetime

register = template.Library()

@register.filter(name='showServerInfo')
def showServerInfo(id):
    '''Show server info'''
    try:
        s = Server.objects.get(id=id)
        result = "server name: %s<br/>core: %s ram: %s hard disk: %s" % (s.name,s.core,s.ram,s.hard_disk)
    except:
        result = ""
        
    return result

@register.filter(name='tr_color')
def tr_color(row_number):
    '''decide <tr> color'''
    if row_number % 2 == 0:
        return True
    else:
        return False
    