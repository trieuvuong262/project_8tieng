from django.contrib import admin
from django.urls import path, include
from django.conf import settings             # <--- Thêm dòng này
from django.conf.urls.static import static   # <--- Thêm dòng này
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # Trỏ về app core
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)