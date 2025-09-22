from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path("", views.home, name="home"),
    path("register/", views.registerUser, name="register"),
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # Dashboard & Profile
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("iterinary/", views.iterinary, name="iterinary"),
    path("profile/", views.profile_view, name="profile"),

    # Clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_update, name="client_update"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),

    # Bookings
    path("bookings/", views.BookingListView.as_view(), name="booking_list"),
    path("bookings/new/", views.BookingCreateView.as_view(), name="booking_create"),
    path("bookings/<int:pk>/", views.BookingDetailView.as_view(), name="booking_detail"),
    path("bookings/<int:pk>/pdf/", views.booking_pdf, name="booking_pdf"),

    # Destinations & related uploads
    path("bookings/<int:booking_id>/destinations/new/", views.DestinationCreateView.as_view(), name="add_destination"),
    path("destinations/<int:pk>/", views.DestinationDetailView.as_view(), name="destination_detail"),
    path("destinations/<int:id>/edit/", views.edit_destination, name="edit_destination"),
    path("destinations/<int:id>/delete/", views.delete_destination, name="delete_destination"),
    path("destinations/<int:pk>/upload-image/", views.upload_destination_image, name="upload_destination_image"),
    path("destinations/<int:destination_id>/activities/new/", views.upload_activity, name="upload_activity"),
    path("destinations/<int:destination_id>/stays/new/", views.upload_stay, name="upload_stay"),
    path("destinations/<int:destination_id>/dining/new/", views.upload_dining_expense, name="upload_dining"),
    path("destinations/<int:destination_id>/restaurants/new/", views.upload_restaurant, name="upload_restaurant"),
    path("bookings/<int:booking_id>/legs/new/", views.upload_travel_leg, name="upload_travel_leg"),

    # Subscriptions (Planner self-service)
    path("my/subscriptions/", views.my_subscriptions, name="my_subscriptions"),
    path("my/subscriptions/add/", views.my_subscription_create, name="my_subscription_create"),
    path("my/subscriptions/<int:pk>/edit/", views.my_subscription_edit, name="my_subscription_edit"),

    # PayPal Payment
    path("payment/<int:subscription_id>/", views.create_payment, name="create_payment"),
    path("payment/execute/", views.execute_payment, name="execute_payment"),

    # Subscriptions (Admin-managed)
    path("planners/", views.planner_list, name="planner_list"),
    path("planners/<int:profile_id>/subscriptions/", views.subscription_list, name="subscription_list"),
 
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/admin/planner/<int:profile_id>/", views.admin_planner_detail, name="admin_planner_detail"),
    path("dashboard/admin/subscription/<int:sub_id>/edit/", views.admin_subscription_edit, name="admin_subscription_edit"),
    path("dashboard/admin/subscription/<int:sub_id>/toggle/", views.admin_subscription_toggle, name="admin_subscription_toggle"),
    path("booking/<int:booking_id>/add-traveler/", views.add_traveler, name="add_traveler"),
]