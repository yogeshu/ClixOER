from django.conf.urls import patterns, url

urlpatterns = patterns('gnowsys_ndf.ndf.views.domain',

						url(r'^[/]$', 'domain_page', name='domain_page')
 )