from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^v(?P<api_version>\d+)/index/$', 'api.views.index')
)