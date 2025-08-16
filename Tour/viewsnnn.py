from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Q, Prefetch
from .models import Restaurant, Client,Booking, Destination, Activity, Stay, DiningExpense, TravelLeg
from .models import Booking, Destination, Activity, Stay, DiningExpense, TravelLeg
from .forms import BookingForm, DestinationForm

# ---------- Public pages ----------
def home(request):
    return render(request, "tour/home.html")

# ---------- Auth ----------
from .forms import PlannerCreationForm

def registerUser(request):
    if request.user.is_authenticated:
        return redirect("booking_list")

    form = PlannerCreationForm()
    if request.method == "POST":
        form = PlannerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Planner account created. You’re now logged in.")
            login(request, user)
            return redirect("booking_list")
        else:
            messages.error(request, "There was a problem creating your account.")
    return render(request, "tour/register.html", {"form": form})

def loginPage(request):
    if request.user.is_authenticated:
        return redirect("booking_list")

    if request.method == "POST":
        username = (request.POST.get("username") or "").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "booking_list")
        messages.error(request, "Invalid username or password.")
    return render(request, "tour/login.html")

@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")





@login_required
def dashboard(request):
    bookings = Booking.objects.select_related("client").order_by("-created_at")[:20]
    return render(request, "tour/dashboard.html", {"bookings": bookings})


# ---------- client pages ----------

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClientForm
from .models import Client

def client_list(request):
    clients = Client.objects.all()
    return render(request, "tour/client_list.html", {"clients": clients})

def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
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
                Prefetch("destinations", queryset=Destination.objects.only("id", "name", "start_date", "end_date")),
                "travel_legs",
            )
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
        # Simple per-destination totals (optional)
        accom_total = sum((s.total_cost or 0) for s in dest.stays.all())
        activities_total = sum((a.cost or 0) for a in dest.activities.all())
        dining_total = sum((d.cost or 0) for d in dest.dining_expenses.all())
        ctx["totals"] = {
            "Accommodation": accom_total,
            "Activities": activities_total,
            "Dining": dining_total,
            "Subtotal": accom_total + activities_total + dining_total,
        }
        return ctx
