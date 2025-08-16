from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # auth
    path("register/", views.registerUser, name="register"),
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),

    # bookings
    path("bookings/", views.BookingListView.as_view(), name="booking_list"),
    path("bookings/new/", views.BookingCreateView.as_view(), name="booking_create"),
    path("bookings/<int:pk>/", views.BookingDetailView.as_view(), name="booking_detail"),

    # destination
    path("bookings/<int:booking_id>/destinations/new/", views.DestinationCreateView.as_view(), name="add_destination"),
    path("destinations/<int:pk>/", views.DestinationDetailView.as_view(), name="destination_detail"),
    path("destinations/<int:id>/edit/", views.edit_destination, name="edit_destination"),
    path("destinations/<int:id>/delete/", views.delete_destination, name="delete_destination"),

    # uploads (child records)
    path("destinations/<int:destination_id>/activities/new/", views.upload_activity, name="upload_activity"),
    path("destinations/<int:destination_id>/stays/new/", views.upload_stay, name="upload_stay"),
    path("destinations/<int:destination_id>/dining/new/", views.upload_dining_expense, name="upload_dining"),
    path("destinations/<int:destination_id>/restaurants/new/", views.upload_restaurant, name="upload_restaurant"),
    path("bookings/<int:booking_id>/legs/new/", views.upload_travel_leg, name="upload_travel_leg"),
]
