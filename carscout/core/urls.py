from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
   path('signup/',views.UserSignupView,name='signup'),
   path('login/',views.UserLoginView,name='login'),
   path('logout/',views.user_logout,name='logout'),
   path('',views.home,name='home')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



