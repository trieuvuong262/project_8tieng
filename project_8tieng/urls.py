from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <--- QUAN TRỌNG
from django.conf.urls.static import static # <--- QUAN TRỌNG

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# ĐOẠN NÀY BẮT BUỘC PHẢI CÓ ĐỂ UPLOAD ẢNH
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)