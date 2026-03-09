from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from scout.views import CreateAdminView

urlpatterns = [
   path('signup/',views.UserSignupView,name='signup'),
   path('login/',views.UserLoginView,name='login'),
   path('logout/',views.user_logout,name='logout'),
   path('createadmin/',CreateAdminView,name='create_admin'),
   path('',views.home,name='home')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



