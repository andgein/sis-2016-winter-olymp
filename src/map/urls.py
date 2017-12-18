from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^tile/(?P<tile_id>\d+)/$', views.read_tile, name='tile'),
    url(r'^tile/(?P<tile_id>\d+)/statement/$', views.read_statement, name='statement'),
    url(r'^bonus/(?P<tile_id>\d+)/use/(?P<selected_tile_id>.+)/$', views.use_bonus, name='use_bonus'),
    # url(r'^runs/$', views.runs, name='runs'),
]
