from datetime import timedelta
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Q, Prefetch

from .models import (
    Client, Booking, Destination, Activity, Stay, DiningExpense, TravelLeg, Restaurant
)
from .forms import (
    PlannerCreationForm,
    ClientForm, BookingForm, DestinationForm,
    ActivityForm, StayForm, DiningExpenseForm, RestaurantForm, TravelLegForm
)

# ---------- Public ----------
def home(request):
    return render(request, "tour/home.html")


# ---------- Auth ----------
def registerUser(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = PlannerCreationForm()
    if request.method == "POST":
        form = PlannerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Planner account created. You’re now logged in.")
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "There was a problem creating your account.")
    return render(request, "tour/register.html", {"form": form})


def loginPage(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = (request.POST.get("username") or "").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "tour/login.html")


@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    """
    Shows recent bookings + their destinations, with quick-add links.
    """
    bookings = (
        Booking.objects
        .select_related("client")
        .prefetch_related(
            Prefetch("destinations", queryset=Destination.objects.order_by("start_date"))
        )
        .order_by("-created_at")[:20]
    )
    return render(request, "tour/dashboard.html", {"bookings": bookings})


# ---------- Client pages ----------
@login_required
def client_list(request):
    clients = Client.objects.all().order_by("name")
    return render(request, "tour/client_list.html", {"clients": clients})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client created.")
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(request, "tour/client_form.html", {"form": form})


# ---------- Booking pages ----------
@method_decorator(login_required, name="dispatch")
class BookingListView(ListView):
    model = Booking
    template_name = "tour/booking_list.html"
    context_object_name = "bookings"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        qs = (
            Booking.objects
            .select_related("client")
            .prefetch_related(
                Prefetch("destinations", queryset=Destination.objects.only(
                    "id", "name", "start_date", "end_date"
                )),
                "travel_legs",
            )
            .order_by("-created_at")
        )
        if q:
            qs = qs.filter(
                Q(client__name__icontains=q) |
                Q(client__email__icontains=q) |
                Q(client__phone__icontains=q) |
                Q(destinations__name__icontains=q)
            ).distinct()
        return qs


@method_decorator(login_required, name="dispatch")
class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "tour/booking_form.html"

    def get_success_url(self):
        return reverse("booking_detail", kwargs={"pk": self.object.pk})


@method_decorator(login_required, name="dispatch")
class BookingDetailView(DetailView):
    model = Booking
    template_name = "tour/booking_detail.html"
    context_object_name = "booking"

    def get_queryset(self):
        return (
            Booking.objects
            .select_related("client")
            .prefetch_related(
                Prefetch("destinations", queryset=Destination.objects.all()),
                Prefetch("travel_legs", queryset=TravelLeg.objects.select_related("from_destination", "to_destination"))
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        booking: Booking = ctx["booking"]
        ctx["costs"] = booking.cost_breakdown()
        ctx["destinations"] = booking.destinations.all().order_by("start_date")
        return ctx


# ---------- Destination pages ----------
@method_decorator(login_required, name="dispatch")
class DestinationCreateView(CreateView):
    """
    URL must include booking_id param; we attach the new Destination to that booking.
    """
    model = Destination
    template_name = "tour/destination_form.html"
    form_class = DestinationForm

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=kwargs["booking_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["booking"] = self.booking
        return kwargs

    def form_valid(self, form):
        form.instance.booking = self.booking
        messages.success(self.request, "Destination added to booking.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("booking_detail", kwargs={"pk": self.booking.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["booking"] = self.booking
        return ctx


@method_decorator(login_required, name="dispatch")
class DestinationDetailView(DetailView):
    model = Destination
    template_name = "tour/destination_detail.html"
    context_object_name = "destination"

    def get_queryset(self):
        return (
            Destination.objects.select_related("booking", "booking__client")
            .prefetch_related(
                Prefetch("stays", queryset=Stay.objects.all()),
                Prefetch("activities", queryset=Activity.objects.all().order_by("date", "start_time")),
                Prefetch("dining_expenses", queryset=DiningExpense.objects.select_related("restaurant")),
                Prefetch("restaurants", queryset=Restaurant.objects.all()),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dest: Destination = ctx["destination"]

        # compute day-by-day list from destination dates (no date_ranges model)
        days = []
        current = dest.start_date
        while current <= dest.end_date:
            day_activities = dest.activities.filter(date=current).order_by("start_time")
            days.append({"date": current, "activities": day_activities})
            current += timedelta(days=1)

        # simple totals just for this destination
        accom_total = sum((s.total_cost or 0) for s in dest.stays.all())
        activities_total = sum((a.cost or 0) for a in dest.activities.all())
        dining_total = sum((d.cost or 0) for d in dest.dining_expenses.all())

        ctx["totals"] = {
            "Accommodation": accom_total,
            "Activities": activities_total,
            "Dining": dining_total,
            "Subtotal": accom_total + activities_total + dining_total,
        }

        ctx["tab_labels"] = ["Overview","Gallery", "Stays", "Activities", "Dining", "Transport", "Map","Costs"]
        ctx["itinerary_days"] = days
        return ctx


@login_required
def edit_destination(request, id):
    destination = get_object_or_404(Destination, id=id)
    if request.method == "POST":
        form = DestinationForm(request.POST, instance=destination, booking=destination.booking)
        if form.is_valid():
            form.save()
            messages.success(request, "Destination updated.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = DestinationForm(instance=destination, booking=destination.booking)
    return render(request, "tour/edit_destination.html", {"form": form, "destination": destination})


@login_required
def delete_destination(request, id):
    destination = get_object_or_404(Destination, id=id)
    if request.method == "POST":
        booking_id = destination.booking_id
        destination.delete()
        messages.info(request, "Destination deleted.")
        return redirect("booking_detail", pk=booking_id)
    return render(request, "tour/delete_destination.html", {"destination": destination})


# ---------- Upload/Add child records (aligned to current models) ----------
@login_required
def upload_activity(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if request.method == "POST":
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.destination = destination
            activity.save()
            messages.success(request, "Activity added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = ActivityForm(initial={"destination": destination})
        form.fields["destination"].widget = forms.HiddenInput()
    return render(request, "tour/upload_activity.html", {"form": form, "title": "Add Activity", "destination": destination})


@login_required
def upload_stay(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if request.method == "POST":
        form = StayForm(request.POST)
        if form.is_valid():
            stay = form.save(commit=False)
            stay.destination = destination
            stay.save()  # total_cost computed in model.save()
            messages.success(request, "Stay added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = StayForm(initial={"destination": destination})
        form.fields["destination"].widget = forms.HiddenInput()
    return render(request, "tour/upload_stay.html", {"form": form, "title": "Add Stay", "destination": destination})


@login_required
def upload_dining_expense(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if request.method == "POST":
        form = DiningExpenseForm(request.POST)
        if form.is_valid():
            de = form.save(commit=False)
            de.destination = destination
            de.save()
            messages.success(request, "Dining expense added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = DiningExpenseForm(initial={"destination": destination})
        form.fields["destination"].widget = forms.HiddenInput()
    return render(request, "tour/upload_dining.html", {"form": form, "title": "Add Dining Expense", "destination": destination})


@login_required
def upload_restaurant(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if request.method == "POST":
        form = RestaurantForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.destination = destination
            r.save()
            messages.success(request, "Restaurant added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = RestaurantForm(initial={"destination": destination})
        form.fields["destination"].widget = forms.HiddenInput()
    return render(request, "tour/upload_restaurant.html", {"form": form, "title": "Add Restaurant", "destination": destination})


@login_required
def upload_travel_leg(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        form = TravelLegForm(request.POST)
        if form.is_valid():
            leg = form.save(commit=False)
            leg.booking = booking
            leg.save()
            messages.success(request, "Travel leg added.")
            return redirect("booking_detail", pk=booking.id)
    else:
        form = TravelLegForm(initial={"booking": booking})
        form.fields["booking"].widget = forms.HiddenInput()

        # optional: restrict from/to destination choices to this booking
        form.fields["from_destination"].queryset = booking.destinations.all()
        form.fields["to_destination"].queryset = booking.destinations.all()

    return render(request, "tour/upload_travel_leg.html", {"form": form, "title": "Add Travel Leg", "booking": booking})
