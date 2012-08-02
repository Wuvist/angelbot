from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^AngelWeb/', include('AngelWeb.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^$', 'views.home'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^servers/(\d+)/$', 'servers.views.show'),
    (r'^servers/(\d+)/(\d+)/$', 'servers.views.show_cmd'),
    (r'^servers/(\d+)/exe/(\d+)$', 'servers.views.execute_cmd'),
    (r'^rrd/$', 'servers.views.rrd_list'),    
    (r'^rrd/img/(\d+)/$', 'servers.views.rrd_img'),
    (r'^rrd/(\d+)/$', 'servers.views.rrd_show'),
    (r'^dashboard/(\d+)/widget/(\d+)/graph$', 'servers.views.rrd_show_widget_graph'),
    (r'^rrd/img/(\d+)/download$', 'servers.views.rrd_download'),    
    (r'^rrd/(\d+)/create$', 'servers.views.rrd_create'),    
    (r'^dashboard/(\d+)/$', 'servers.views.dashboard_show'),
    (r'^parse/$', 'servers.views.parser'),
    (r'^dashboard/(\d+)/widget/(\d+)/parse/$', 'servers.views.show_parse_graph'),
    (r'^downloadparse/$', 'servers.views.parse_downoad'),
    (r'^grahaiderimg/(\d+)/w/(\d+)/h/(\d+)/start/(\d+)/end/(\d+)$', 'servers.views.grah_aider_img'),
    (r'^graphaider/(\d+)/$', 'servers.views.graph_aiders'),
    (r'^alarm/$', 'servers.views.alarm'),
    (r'^dashboard/error/(\d+)/$', 'servers.views.dashboard_show_error'),
    (r'^assort', 'servers.views.show_assort_widget'),
    (r'^cmdb/servers/$', 'cmdb.views.show_servers'),
    (r'^cmdb/updateservers/$', 'cmdb.views.syncdbservers'),
    (r'^cmdb/services/$', 'cmdb.views.show_services'),
    (r'^cmdb/updateservices/$', 'cmdb.views.syncdbservices'),
    (r'^cmdb/deployment/$', 'cmdb.views.cmdbDeployment'),
    (r'^statistics/update/$', 'servers.viewstatistics.statistics_update'),
    (r'^statistics/show/$', 'servers.viewstatistics.statistics_show'),
    (r'^statistics/show/addcomment/$', 'servers.viewstatistics.addComment'),
    (r'^statistics/show/download/$', 'servers.viewstatistics.statistics_show_download'),
    (r'^ticket/$', 'servers.viewstatistics.ticket'),
    (r'^ticket/show/(\d+)$', 'servers.viewstatistics.ticket_show'),
    
)
