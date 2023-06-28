from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),

    path('post/add/', views.post_add, name='post_add'),
    path('post/<int:id>/', views.post_view, name='post_view'),
    path('post/<int:id>/like/', views.post_like, name='post_like'),
    path('post/<int:id>/comment/', views.post_comment, name='post_comment'),
    path('upload/', views.analyze),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
