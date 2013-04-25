from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'bwsport.views.home', name='home'),
    # url(r'^bwsport/', include('bwsport.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'projects/$','servers.overviews.projects'),
    (r'projects/showdetail/service/(\d+)$','servers.overviews.showdetail_services'),
    (r'project/(\d+)$','servers.overviews.project_servers'),
    (r'project/(\d+)/server/(\d+)/$','servers.overviews.project_server'),
)