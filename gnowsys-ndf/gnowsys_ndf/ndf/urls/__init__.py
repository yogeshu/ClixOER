from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
# from django.views.generic import RedirectView

from registration.backends.default.views import RegistrationView
from registration.backends.default.views import ActivationView
from jsonrpc import jsonrpc_site

# from gnowsys_ndf.ndf.forms import *
from gnowsys_ndf.settings import GSTUDIO_SITE_NAME,GSTUDIO_USERNAME_SELECTION_WIDGET, GSTUDIO_OER_GROUPS
from gnowsys_ndf.ndf.views.email_registration import password_reset_email, password_reset_error, GstudioEmailRegistrationForm
from gnowsys_ndf.ndf.forms import UserChangeform, UserResetform
#from gnowsys_ndf.ndf.views.home import homepage, landing_page
from gnowsys_ndf.ndf.views.methods import tag_info
from gnowsys_ndf.ndf.views.custom_app_view import custom_app_view, custom_app_new_view
from gnowsys_ndf.ndf.views import rpc_resources
if GSTUDIO_SITE_NAME.lower() == 'clix':
    login_template = 'registration/login_clix.html'
    logout_template = "ndf/landing_page_clix_oer.html"
else:
    login_template = 'registration/login.html'
    logout_template = 'registration/logout.html'

urlpatterns = patterns('',
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^pref_lang/$', include('gnowsys_ndf.ndf.urls.languagepref')),

    # gstudio admin url's
    (r'^admin/', include('gnowsys_ndf.ndf.urls.gstudio_admin')),

    # django-registration
    url(r'^accounts/password/change/done/', auth_views.password_change_done, {'template_name': 'registration/password_change_done.html'}, name='password_change_done'),
    url(r'^accounts/password/change/', auth_views.password_change, {'password_change_form': UserChangeform, 'template_name': 'registration/password_change_form.html'}),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {'set_password_form': UserResetform},name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^accounts/password/reset/done/$',auth_views.password_reset_done,name="password_reset_done"),
    url(r'^accounts/password/reset/error/$', password_reset_error , name='password_reset_error'),
    url(r'^accounts/password/reset/$',
        password_reset_email,
        {
            'template_name': 'registration/password_reset_form.html',
            'email_template_name': 'registration/password_reset_email.html',
            'subject_template_name':'registration/password_reset_email_subject.txt'
        },
        name='password_reset'
    ),

    url(r'^accounts/activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(
            template_name='registration/activation_complete.html',
            get_success_url=getattr(
                settings, 'REGISTRATION_EMAIL_ACTIVATE_SUCCESS_URL',
                lambda request, user: '/accounts/activate/complete/'),
        ),
        name='registration_activate'),

    url(r'^accounts/register/$',
        RegistrationView.as_view(
            form_class=GstudioEmailRegistrationForm,
            get_success_url=getattr(
                settings, 'REGISTRATION_EMAIL_REGISTER_SUCCESS_URL',
                lambda request, user: '/accounts/register/complete/'),
        ),
        name='registration_register'),

    # url(r'^accounts/login/$', auth_views.login ,{'template_name': login_template}, name='login'),
    url(r'^accounts/login/$', auth_views.login ,{'template_name': login_template, 'extra_context': {'USERNAME_SELECTION_WIDGET': GSTUDIO_USERNAME_SELECTION_WIDGET}}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout ,{'template_name': logout_template }, name='logout'),
    url(r'^accounts/', include('registration.backends.default.urls')),

   # --end of django-registration

   (r'^status/cache/$', 'gnowsys_ndf.ndf.views.cache.cache_status'),
)
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
)
from gnowsys_ndf.ndf.views.es_queries import homepage
urlpatterns += patterns('gnowsys_ndf.ndf.views.es_queries',
                        url(r'^$', homepage, {"group_id": "home"}, name="homepage"),
                        url(r'^(?P<group_id>[^/]+)/?$', homepage, name="homepage1"),
                        url(r'^(?P<group_id>[^/]+)/e-library', include('gnowsys_ndf.ndf.urls.e-library')),
                        url(r'^(?P<group_id>[^/]+)/module/(?P<node_id>[\w-]+)/(?P<title>[^/]+)/?$', 'module_detail', name='module_detail'),
                        url(r'^(?P<group_id>[^/]+)/course/save_course_page/$', 'save_course_page', name='save_course_page'),
                        #url(r'^(?P<group_id>[^/]+)/course/content/$', 'course_content', name='course_content'),
                        #url(r'^(?P<group_id>[^/]+)/course/activities/$', 'course_pages', name='course_pages'),
                        #url(r'^(?P<group_id>[^/]+)/course/activities/page-no=(?P<page_no>\d+)/$', 'course_pages', name='course_pages_paged'),
                        #url(r'^(?P<group_id>[^/]+)/course/activity/detail/(?P<page_id>[\w-]+)$', 'course_pages', name='view_course_page'),
                        #url(r'^(?P<group_id>[^/]+)/course/activity/create$', 'create_edit_course_page', name='create_course_page'),
                        #url(r'^(?P<group_id>[^/]+)/unit/lessons/$', 'unit_detail', name='unit_detail'),
                        #url(r'^(?P<group_id>[^/]+)/unit//lesson/create/?$', 'lesson_create_edit', name='lesson_create_edit'),
                        #url(r'^(?P<group_id>[^/]+)/ajax/get_group_resources/(?P<res_type>[\w-]+)$', 'get_group_resources', name='get_group_resources'),
                        url(r'^(?P<group_id>[^/]+)/ajax/module/$', 'get_module_previewdata', name='get_module_previewdata'),
                        url(r'^(?P<group_id>[^/]+)/domain/(?P<domain_name>[^/]+)/$', 'domain_page', name='domain_page'),
                        url(r'^(?P<group_id>[^/]+)/file/uploadDoc/$', 'uploadDoc', name='uploadDoc'),
                        url(r'^(?P<group_id>[^/]+)/domain/(?P<domain_name>[^/]+)/Design_Development/$', 'loadDesignDevelopment', name='designDev'),
                        url(r'^(?P<group_id>[^/]+)/about/$', 'about', name='about'),
                        url(r'^(?P<group_id>[^/]+)/domain/(?P<domain_name>[^/]+)/help/$', 'domain_help', name='domainHelp'),
                        url(r'^(?P<group_id>[^/]+)/file/readDoc/(?P<file_id>[\w-]+)/$', 'readDoc', name='read_file'),
                        url(r'^(?P<group_id>[^/]+)/ajax/send_message/$', 'send_message', name='send_message'),
                        url(r'^(?P<group_id>[^/]+)/help/$', 'help', name='help'),
                        url(r'^(?P<group_id>[^/]+)/ajax/module/help_videos/$', 'help_videos', name='help_videos'),
                        url(r'^(?P<group_id>[^/]+)/ajax/explore/$', 'explore_item', name='explore_link'),
                        url(r'^(?P<group_id>[^/]+)/ajax/module/lang$', 'fetch_modules_of_language', name='language_modules'),
                        #url(r'^(?P<group_id>[^/]+)/create/module/$','create_lang_module',name='create_module'),
                        #url(r'^(?P<group_id>[^/]+)/create/unit/$','create_lang_unit',name='create_unit'),
                        #url(r'^(?P<group_id>[^/]+)/node/create/(?P<member_of>[\w-]+)/(?P<detail_url_name>[\w-]+)/?$', 'node_create_edit', {'node_type': 'GSystem', 'node_id': None}, name='node_create'),
                        #url(r'^(?P<group_id>[^/]+)/node/edit/(?P<node_id>[\w-]+)/$', 'node_name_content_edit', name='node_edit'),
                        url(r'^(?P<group_id>[^/]+)/upload_using_save_file/', 'upload_using_save_file', name='upload_using_save_file'),
                        url(r'^contact.html/','site_contact',name='site_contact'),
                        url(r'^termsofservice.html/','site_termsofuse',name='site_termsofuse'),
                        url(r'^privacypolicy.html/','site_privacypolicy',name='site_privacypolicy')
                        )
