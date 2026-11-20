# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# accounts থেকে home_view ইমপোর্ট করুন, dashboard থেকে নয়
from accounts.views import home_view 

urlpatterns = [
    # রুট URL এখন ল্যান্ডিং পেজে যাবে
    path("", home_view, name="home"), 
    
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("complaints/", include("complaints.urls", namespace="complaints")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)