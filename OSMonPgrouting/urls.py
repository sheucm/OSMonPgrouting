from django.conf.urls import patterns, include, url
from django.contrib import admin
from testPG.views import test_pg
from routing.views import do_routing, index

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'OSMonPgrouting.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^test/$', test_pg),
    url(r'^do_routing/$', do_routing),
	url(r'^$', index),
)
