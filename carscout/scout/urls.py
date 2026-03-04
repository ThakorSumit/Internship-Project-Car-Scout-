from django.urls import path
from . import views

urlpatterns = [
    # Admin
    path('admin/', views.AdminDashboardView, name='admin_dashboard'),

    # Seller
    path('seller/', views.SellerDashboardView, name='seller_dashboard'),
    path('seller/add-listing/', views.AddListingView, name='add_listing'),
    path('seller/listing/<int:listing_id>/', views.SellerListingDetailView, name='seller_listing_detail'),
    path('seller/listing/<int:listing_id>/delete/', views.DeleteListingView, name='delete_listing'),

    # Buyer
    path('buyer/', views.BuyerDashboardView, name='buyer_dashboard'),
]