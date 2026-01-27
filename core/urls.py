# core/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # <--- Import thêm cái này

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='home'),
    
    # Gamification
    path('checkin/', views.daily_checkin, name='daily_checkin'),
    
    # Zone 3: Confession
    path('social/', views.confession_feed, name='confession_feed'),
    path('social/api/like/<int:post_id>/', views.api_like_confession, name='api_like_confession'),
    path('social/api/react/<int:post_id>/<str:reaction_type>/', views.api_react_confession, name='api_react_confession'),
    
    path('social/comment/<int:post_id>/', views.submit_comment, name='submit_comment'),
    # Các Zone khác (Placeholder - Làm sau)
    # path('productivity/', views.productivity_zone, name='productivity'),
    # path('pantry/', views.pantry_zone, name='pantry'),
    # path('shop/', views.shop_zone, name='shop'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('admin-panel/', views.moderation_dashboard, name='moderation_dashboard'),
    path('register/', views.register, name='register'),
    path('profile/', views.my_profile, name='my_profile'),
    # [MỚI] API Báo cáo bài viết
    path('social/report/<int:post_id>/', views.api_report_post, name='report_post'),
    
    # [MỚI] API Ẩn bài viết
    path('social/hide/<int:post_id>/', views.api_hide_post, name='hide_post'),
]