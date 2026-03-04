from django.urls import path
from . import views

urlpatterns = [
   path('admin/', views.AdminDashboardView, name='admin_dashboard'),
   path('seller/', views.SellerDashboardView, name='seller_dashboard'),
   path('buyer/', views.BuyerDashboardView, name='buyer_dashboard'),
   path('seller/add-vehicle/', views.add_vehicle, name='add_vehicle'),           # ← step 1
   path('seller/select-vehicle/', views.select_vehicle, name='select_vehicle'),
   path('seller/create-listing/<int:vehicle_id>/', views.listing, name='listing'), # ← step 2
   path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
   path('admin/inspection-report/', views.inspection_report, name='inspection_report'),
   path('buyer/test-drive/<int:listing_id>/', views.test_drive, name='test_drive'),
   path('buyer/offer/<int:listing_id>/', views.offer, name='offer'),
   path('admin/transaction/', views.transaction, name='transaction'),
]