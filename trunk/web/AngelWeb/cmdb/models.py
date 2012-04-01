from django.db import models

# Create your models here.

SERVER_TYPE_CHOICES = (
    ('W', 'Windows'),
    ('L', 'Linux'),
)

YES_OR_NO_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No'),
)

SERVER_FUNCTION_CHOICES = (
    ('D', 'DB'),
    ('A', 'APP'),
)

class Server(models.Model):
    ip = models.IPAddressField(max_length=200)
    server_id = models.IntegerField(max_length=8)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    project = models.CharField(max_length=50)
    physical_server = models.CharField(max_length=1, choices=YES_OR_NO_CHOICES)
    physical_server_ip = models.IPAddressField(max_length=32)
    core = models.IntegerField(max_length=2)
    ram = models.CharField(max_length=10)
    hard_disk = models.CharField(max_length=100)
    server_function = models.CharField(max_length=1, default="A", choices=SERVER_FUNCTION_CHOICES)
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    idc = models.CharField(max_length=64, null = True, blank = True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    available = models.CharField(max_length=1, default="Y", choices=YES_OR_NO_CHOICES)
    del_time = models.DateTimeField(null = True, blank = True)
    created_on = models.DateTimeField(null = True, blank = True)
    
    def __unicode__(self):
        return self.name + "(" + str(self.ip) + ")"
    
    class Meta:
        ordering = ["ip"]
    
class Service(models.Model):
    title = models.CharField(max_length=50)
    service_id = models.IntegerField(max_length=16)
    server_id = models.CharField(max_length=8) 
    project = models.CharField(max_length=50)
    dashboard = models.CharField(max_length=32, null = True, blank = True)
    ip = models.IPAddressField(max_length=64)
    physical_server_ip = models.IPAddressField(max_length=64)
    system = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    service_name = models.CharField(max_length=50)
    service_type = models.CharField(max_length=50)
    path = models.CharField(max_length=128, null = True, blank=True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    available = models.CharField(max_length=1, default="Y", choices=YES_OR_NO_CHOICES)
    del_time = models.DateTimeField(null = True, blank = True)
    update_time = models.DateTimeField(null = True, blank = True)
    created_on = models.DateTimeField(null = True, blank = True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]
        
class LastUpdate(models.Model):
    title = models.CharField(max_length=50)
    created_on = models.DateTimeField(null = True, blank = True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]
