from django.urls import path
from . import views

urlpatterns = [
   path('signup/',views.UserSignupView,name='signup'),
   path('login/',views.UserLoginView,name='login'),
   path('logout/',views.user_logout,name='logout'),
   path('',views.home,name='home'),
]
