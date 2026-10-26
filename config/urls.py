from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Server-rendered storefront (templates)
    path('', include('storefront.urls', namespace='storefront')),
    path('compare/', include('compare.urls', namespace='compare')),
    path('pages/', include('pages.urls', namespace='pages')),

    # REST API v1
    path('api/v1/', include('config.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
