from django.urls import path
from . import views

# urls.py
from django.urls import path
# from .views import planner

urlpatterns = [
    path('',views.home,name='home'),
    path('login/',views.loginPage,name='login'),
    path('logout/',views.logout_user,name='logout'),
    path('register/',views.registerUser,name='register'),
    path('dashboard/',views.dashboard,name='dashboard'),
     
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/add/', views.BookingCreateView.as_view(), name='booking_add'),
    path('bookings/<int:booking_id>/destinations/add/', views.DestinationCreateView.as_view(), name='destination_add'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('destinations/<int:pk>/', views.DestinationDetailView.as_view(), name='destination_detail'),
]


# urlpatterns=[
#     path('',views.home,name='home'),
#     path('login/',views.loginPage,name='login'),
#     path('logout/',views.logoutUser,name='logout'),
#     path('register/',views.registerUser,name='register'),
#     path('dashboard/',views.dashboard,name='dashboard'), 
#     path('profile/<str:pk>/',views.userProfile,name='profile'),
#     path('clientList/',views.clientList,name='clientList'), 
#     path('client/<int:pk>/',views.clientDetails,name='clientDetails'),       
#     path('itinerary/',views.itinerary,name='itinerary'),
#     path('newBooking/',views.newBooking,name='newBooking'),
#     path('newItinerary/',views.newItinerary,name='newItinerary'),
#     path('updateBooking/<str:pk>/',views.updateBooking,name='updateBooking'),
#     path('updateItinerary/<str:pk>/',views.updateItinerary,name='updateItinerary'),
#     path('deleteBooking/<str:pk>/',views.deleteBooking,name='deleteBooking'),
#     path('deleteItinerary/<str:pk>/',views.deleteItinerary,name='deleteItinerary'),

    
#     path('homee', views.homepage, name='homee'),
#     path('logout/', views.logout_view, name='logout'),
#     path('destinations/', views.all_destinations, name='all_destinations'),  # This is the fix
#     path('destination_list', views.destination_list, name='destination_list'),
#     path('dashboardm/', views.dashboard_view, name='dashboardm'),
#     path('destination/<int:id>/', views.destination_detail, name='destination_detail'),
#     path('accommodation_summary_view', views.accommodation_summary_view, name='accommodation_summary_view'),
#     path('destination/add/', views.add_destination_view, name='add_destination'),
#     path('register/', views.register_view, name='register'), 
#     path('destination/<int:destination_id>/upload/', views.upload_images, name='upload_image'),
    
#     path('destination/<int:destination_id>/upload/gallery/', views.upload_gallery_image, name='upload_gallery'),
#     path('destination/<int:destination_id>/upload/room/', views.upload_room, name='upload_room'),
#     path('destination/<int:destination_id>/upload/restaurant/', views.upload_restaurant, name='upload_restaurant'),

#     path('destination/<int:id>/edit/', views.edit_destination, name='edit_destination'),
#     path('destination/<int:id>/delete/', views.delete_destination, name='delete_destination'),
    
    
#     path('destination/<int:destination_id>/upload-activity/', views.upload_activity, name='upload_activity'),
#     path('destination/<int:destination_id>/upload-information/', views.upload_information, name='upload_information'),


#     path('accommodation-summary/', views.accommodation_summary_view, name='accommodation_summary'),
#     path('export-summary/excel/', views.export_summary_excel, name='export_summary_excel'),
#     path('export-summary/pdf/', views.export_summary_pdf, name='export_summary_pdf'),
#     path('explore/', views.public_dashboard_view, name='public_dashboard'),
    
#     path('api/travel-dates/<int:destination_id>/', views.get_travel_dates, name='get_travel_dates'),

#     path('summary/', views.client_summary_view, name='client_summary'),
#     path('summary/export/excel/', views.export_summary_excel, name='export_summary_excel'),
#     path('summary/export/pdf/', views.export_summary_pdf, name='export_summary_pdf'),
#     path('travel-leg/create/', views.travel_leg_create, name='travel_leg_create'),
#     path('travel-leg/list/', views.travel_leg_list, name='travel_leg_list'),

#     # Summary page
#     path('travel-summary/', views.travel_summary, name='travel_summary'),

# ]