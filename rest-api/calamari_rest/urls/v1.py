from django.conf.urls import patterns, include, url
from rest_framework import routers
from rest_framework.authtoken import views
import calamari_rest.views.v1

router = routers.DefaultRouter(trailing_slash=False)

# In v1, the user/ URL existed but did almost nothing, it only supported GET and told
# you your current username.
# In v2, the view gets filled out to return the displayname and email address to, and support
# PUT/PATCH operations for users to change their passwords
router.register(r'user', calamari_rest.views.v1.UserViewSet)

router.register(r'group', calamari_rest.views.v1.GroupViewSet)

# The cluster view exists in both v1 and v2
# In v1 the update time was given as both an ISO9601 time and a unix timestamp
# In v2 all times are given in ISO9601 only.
router.register(r'cluster', calamari_rest.views.v1.ClusterViewSet, base_name='cluster')


urlpatterns = patterns(
    '',

    # In v1 this required a POST but also allowed GET for some reason
    # In v2 it's post only
    url(r'^auth/login', calamari_rest.views.v1.login),
    # In v1 this could be operated with a GET or a POST
    # In v2 it's POST only
    url(r'^auth/logout', calamari_rest.views.v1.logout),

    url(r'^token/', views.obtain_auth_token),

    # This has to come after /user/me to make sure that special case is handled
    url(r'^', include(router.urls)),

    # In v1 this contained junk data with fields 'version', 'license', 'registered', 'hostname' and 'ipaddr'
    # In v2 'license' and 'registered' are removed, and 'fqdn' is added, the rest are populated with real data
    url(r'^info', calamari_rest.views.v1.Info.as_view()),


    # In v1, the Health view gave you the 'health' sync_object and the cluster update time
    # In v2, you can request the sync object by name with /sync_object and you can get the
    # cluster update time from /cluster/<id>
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/health$', calamari_rest.views.v1.Health.as_view({'get': 'get'}), name='cluster-health'),

    # In v1, the HealthCounters view /cluster/<id>/health_counters gave you a JSON object in its 'counters' attribute
    # In v2, you get that information by doing a derived object request for the 'health_counters' object, andyou
    # can get the cluster update time from /cluster/<id>
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/health_counters$', calamari_rest.views.v1.HealthCounters.as_view({'get': 'get'}),
        name='cluster-health-counters'),

    # In v1, the Space view /cluster/<id>/space gave you ceph.cluster.{}.df.[used_bytes|capacity_bytes|free_bytes]
    # In v2, you can get these directly using the TODO view that takes a tuple of stat names and gives you latest values
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/space$', calamari_rest.views.v1.Space.as_view({'get': 'get'}), name='osd-space'),

    # In v2 this no longer has "pg_state" filtering (was unused in UI and relied on expensive PG
    # map traversal)
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/osd$', calamari_rest.views.v1.OSDList.as_view({'get': 'get'}), name='cluster-osd-list'),
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/osd/(?P<osd_id>\d+)$', calamari_rest.views.v1.OSDDetail.as_view({'get': 'get'}),
        name='cluster-osd-detail'),

    # In v1, the /pool view gave you cluster,pool_id,name,quota_max_bytes,quota_max_objects,used_objects,used_bytes
    # In v2, you get more generally, but the used_* fields are gone, you use the (TODO) graphite latest value query
    # to get those.
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/pool$', calamari_rest.views.v1.PoolViewSet.as_view({'get': 'list'}),
        name='cluster-pool-list'),
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/pool/(?P<pool_id>\d+)$', calamari_rest.views.v1.PoolViewSet.as_view({'get': 'retrieve'}),
        name='cluster-pool-detail'),

    # In v1 the server view gave you ('addr', 'hostname', 'name', 'services') and
    # each service gave you ('type', 'service_id', 'name').
    # In v2 all that and more is available, names are a little different and all
    # servers have a 'fqdn' and 'hostname' attribute.  Servers are uniquely
    # identified by FQDN.  In v2 there is also a /grains sub-url which
    # gives you all the salt grains
    url(r'^cluster/(?P<fsid>[a-zA-Z0-9-]+)/server$', calamari_rest.views.v1.ServerViewSet.as_view({'get': 'list'}),
        name='cluster-server-list'),
)
