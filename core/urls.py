from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('checkin/', views.daily_checkin, name='daily_checkin'),
    path('social/', views.confession_feed, name='confession_feed'),
    path('social/api/like/<int:post_id>/', views.api_like_confession, name='api_like_confession'),
    path('social/api/react/<int:post_id>/<str:reaction_type>/', views.api_react_confession, name='api_react_confession'),
    path('social/comment/<int:post_id>/', views.submit_comment, name='submit_comment'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('admin-panel/', views.moderation_dashboard, name='moderation_dashboard'),
    path('register/', views.register, name='register'),
    path('profile/', views.my_profile, name='my_profile'),
    path('social/report/<int:post_id>/', views.api_report_post, name='report_post'),
    path('social/hide/<int:post_id>/', views.api_hide_post, name='hide_post'),
    path('trua-nay-an-gi/', views.lunch_page, name='lunch_page'), 
    path('relax/', views.health_page, name='health_page'),
    path('tool_page/', views.tool_page, name='tool_page'),
    path('shop_page/', views.shop_page, name='shop_page'),
    
    path('tools/convert-document/', views.tool_convert_unified, name='tool_convert_unified'),
]