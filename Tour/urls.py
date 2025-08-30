from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # auth
    path("register/", views.registerUser, name="register"),
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # dashboard
    path("iterinary/", views.iterinary, name="iterinary"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),

    # clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_update, name="client_update"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),


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
    path("destinations/<int:pk>/upload-image/", views.upload_destination_image, name="upload_destination_image"),

    path("destinations/<int:destination_id>/activities/new/", views.upload_activity, name="upload_activity"),
    path("destinations/<int:destination_id>/stays/new/", views.upload_stay, name="upload_stay"),
    path("destinations/<int:destination_id>/dining/new/", views.upload_dining_expense, name="upload_dining"),
    path("destinations/<int:destination_id>/restaurants/new/", views.upload_restaurant, name="upload_restaurant"),
    path("bookings/<int:booking_id>/legs/new/", views.upload_travel_leg, name="upload_travel_leg"),
    
    # reports
    
    path("booking/<int:pk>/", views.BookingDetailView.as_view(), name="booking_detail"),
    path("booking/<int:pk>/pdf/", views.booking_pdf, name="booking_pdf"),


    path("planners/", views.planner_list, name="planner_list"),
    path("planners/<int:profile_id>/subscriptions/", views.subscription_list, name="subscription_list"),
    path("planners/<int:profile_id>/subscriptions/add/", views.subscription_create, name="subscription_create"),
    path("subscriptions/<int:pk>/edit/", views.subscription_edit, name="subscription_edit"),
    path("planner/<int:profile_id>/plans/", views.subscription_plans, name="subscription_plans"),
    
    path("planner/<int:profile_id>/subscribe/<str:plan>/", views.subscription_checkout, name="subscription_checkout"),
    path("subscription/<int:sub_id>/success/", views.subscription_success, name="subscription_success"),
    path("subscription/<int:sub_id>/cancel/", views.subscription_cancel, name="subscription_cancel"),

]
