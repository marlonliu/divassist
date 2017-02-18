from django.conf.urls import include, url
from divassist_web.views import *

from django.contrib.auth import views as auth_views

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^$', login_page),
    url(r'^admin/', admin.site.urls),
    url(r'^logout/$', logout_page),
    url(r'^register/$', register),
    url(r'^home_page/$', home_page),
    url(r'^registration/select_home_station/$', select_home_station),
    # url(r'^rides/add_ride/$', add_ride),
    # url(r'^rides/ride_created/$', ride_created),
    # url(r'^rides/search_rides/$', search_ride),
    # url(r'^rides/view_ride/$', view_ride),
    url(r'^upload_ride/$', add_ride),
    url(r'^rides/ride_created/$', ride_created),
    url(r'^search_ride/$', search_ride),
    url(r'^view_rides/$', view_ride),
]