import os
from django import template
from django.conf import settings
import rrdtool
import datetime

register = template.Library()

@register.filter(name='replaceEnter')
def replaceEnter(s):
    try:
        return s[:5]+s[5:-5].replace("\n","<br>")+s[-5:]
    except:return ""
