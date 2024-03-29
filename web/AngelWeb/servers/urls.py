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
    (r'problem/server$','servers.overviews.problem_server'),
    (r'problem/service/(\d+)$','servers.overviews.problem_service'),
    (r'report/availability/$','servers.overviews.availability'),
    (r'report/availability/project/(\d+)/$','servers.overviews.availability_project_detail'),
    (r'report/availability/server/$','servers.overviews.availability_server'),
    (r'report/availability/server/(\d+)/$','servers.overviews.availability_server_detail'),
    (r'report/availability/service/$','servers.overviews.availability_service'),
    (r'report/availability/trends/perf/$','servers.overviews.availability_trends_perf'),
    (r'report/availability/trends/alert/$','servers.overviews.availability_trends_alert'),
    (r'control/widgetconfig/project/(\d+)/$','servers.overviews.control_widgetconfig'),
    (r'widget/diff_conf/$','servers.overviews.widget_diff_conf'),
    (r'quickview$','servers.overviews.quick_view'),
    (r'quickview/img/$','servers.overviews.quick_view_img'),
    (r'services/$','servers.overviews.overviews_services'),
    (r'services/services_detail/(\d+)$','servers.overviews.services_detail'),
    (r'services/(\d+)/$','servers.overviews.services_type'),
    (r'show_widget/(\d+)/$','servers.overviews.services_type_widget'),
)
