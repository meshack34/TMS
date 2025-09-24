
from django import forms
import datetime
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
import paypalrestsdk
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.utils.decorators import method_decorator
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import get_object_or_404
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.lib.pagesizes import A4
import os
from .models import (
    Client, Booking, Destination,DestinationImage, Activity, Stay, DiningExpense, Traveler, 
    TravelLeg, Restaurant,Profile, Subscription
)

from .forms import (
    PlannerCreationForm,ProfileForm,TravelerForm,
    ClientForm, BookingForm, DestinationForm, DestinationImageForm,
    ActivityForm, StayForm, DiningExpenseForm, RestaurantForm, TravelLegForm, SubscriptionForm, AdminSubscriptionForm
)
from django.db.models import Prefetch, Q 


# ---------- Public ----------
def home(request):
    return render(request, "home.html")


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
def iterinary(request):
    bookings = (
        Booking.objects
        .select_related("client")
        .prefetch_related(
            Prefetch("destinations", queryset=Destination.objects.order_by("start_date"))
        )
        .order_by("-created_at")[:20]
    )
    return render(request, "tour/iterinary.html", {"bookings": bookings})


@login_required
def dashboard_view(request):
    user_profile = request.user.profile

    context = {
        "profile": user_profile,
        "clients_count": Client.objects.count(),
        "bookings_count": Booking.objects.count(),
        "destinations_count": Destination.objects.count(),
        "activities_count": Activity.objects.count(),
        "recent_bookings": Booking.objects.order_by("-created_at")[:5],
    }
    return render(request, "tour/dashboard.html", context)

# ---------- Client pages ----------

@login_required
def client_list(request):
    clients = Client.objects.all().order_by("first_name", "last_name")
    return render(request, "tour/client_list.html", {"clients": clients})

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated successfully.")
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(request, "tour/client_form.html", {"form": form, "client": client})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted successfully.")
        return redirect("client_list")
    return render(request, "tour/client_confirm_delete.html", {"client": client})

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
                Q(client__first_name__icontains=q) |
                Q(client__last_name__icontains=q) |
                Q(client__email__icontains=q) |
                Q(client__phone_number__icontains=q) |
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
                Prefetch("travel_legs", queryset=TravelLeg.objects.select_related("from_destination", "to_destination")),
                Prefetch("travelers", queryset=Traveler.objects.all())
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        booking: Booking = ctx["booking"]

        # existing totals
        ctx["costs"] = booking.cost_breakdown()
        ctx["destinations"] = booking.destinations.all().order_by("start_date")

        # transport summary
        legs = booking.travel_legs.all().select_related(
            "from_destination", "to_destination"
        ).order_by("date", "id")

        total_transport = sum((leg.cost or Decimal("0.00")) for leg in legs)
        by_mode = {}
        for leg in legs:
            by_mode[leg.mode] = by_mode.get(leg.mode, Decimal("0.00")) + (leg.cost or Decimal("0.00"))

        ctx["travel_legs"] = legs
        ctx["travel_summary"] = {
            "count": legs.count(),
            "total": total_transport,
            "by_mode": by_mode,
        }

        # 🔹 NEW: per-traveler breakdown
        travelers = booking.travelers.all().prefetch_related("stays", "activities", "dining_expenses", "travel_legs")
        traveler_costs = []
        for t in travelers:
            stay_total = sum((s.total_cost or Decimal("0.00")) for s in t.stays.all())
            act_total = sum((a.cost or Decimal("0.00")) for a in t.activities.all())
            dining_total = sum((d.cost or Decimal("0.00")) for d in t.dining_expenses.all())
            travel_total = sum((leg.cost or Decimal("0.00")) for leg in t.travel_legs.all())
            traveler_costs.append({
                "traveler": t,
                "Accommodation": stay_total,
                "Activities": act_total,
                "Dining": dining_total,
                "Transport": travel_total,
                "Total": stay_total + act_total + dining_total + travel_total,
            })

        ctx["traveler_costs"] = traveler_costs
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

@login_required
def add_traveler(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        form = TravelerForm(request.POST)
        if form.is_valid():
            traveler = form.save(commit=False)
            traveler.booking = booking
            traveler.save()
            return redirect("booking_detail", pk=booking.id)
    else:
        form = TravelerForm()
    return render(request, "travelers/add_traveler.html", {"form": form, "booking": booking})


@method_decorator(login_required, name="dispatch")
class DestinationDetailView(DetailView):
    model = Destination
    template_name = "tour/destination_detail.html"
    context_object_name = "destination"

    def get_queryset(self):
        return (
            Destination.objects.select_related("booking", "booking__client")
            .prefetch_related(
                Prefetch("galleries", queryset=DestinationImage.objects.all()),
                Prefetch("stays", queryset=Stay.objects.prefetch_related("travelers")),
                Prefetch("activities", queryset=Activity.objects.prefetch_related("travelers").order_by("date", "start_time")),
                Prefetch("dining_expenses", queryset=DiningExpense.objects.select_related("restaurant").prefetch_related("travelers")),
                Prefetch("restaurants", queryset=Restaurant.objects.all()),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dest: Destination = ctx["destination"]

        # day-by-day activities
        days = []
        current = dest.start_date
        while current <= dest.end_date:
            day_activities = dest.activities.filter(date=current).order_by("start_time")
            days.append({"date": current, "activities": day_activities})
            current += timedelta(days=1)

        # totals for this destination
        accom_total = sum((s.total_cost or 0) for s in dest.stays.all())
        activities_total = sum((a.cost or 0) for a in dest.activities.all())
        dining_total = sum((d.cost or 0) for d in dest.dining_expenses.all())

        ctx["totals"] = {
            "Accommodation": accom_total,
            "Activities": activities_total,
            "Dining": dining_total,
            "Subtotal": accom_total + activities_total + dining_total,
        }

        # 🔹 NEW: per-traveler totals for this destination only
        traveler_costs = []
        travelers = dest.booking.travelers.all()
        for t in travelers:
            stay_total = sum((s.total_cost or 0) for s in dest.stays.filter(travelers=t))
            act_total = sum((a.cost or 0) for a in dest.activities.filter(travelers=t))
            dining_total = sum((d.cost or 0) for d in dest.dining_expenses.filter(travelers=t))
            traveler_costs.append({
                "traveler": t,
                "Accommodation": stay_total,
                "Activities": act_total,
                "Dining": dining_total,
                "Total": stay_total + act_total + dining_total,
            })

        ctx["traveler_costs"] = traveler_costs

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
def upload_destination_image(request, pk):
    destination = get_object_or_404(Destination, pk=pk)

    if request.method == "POST":
        form = DestinationImageForm(request.POST, request.FILES)
        if form.is_valid():
            dest_img = form.save(commit=False)
            dest_img.destination = destination
            dest_img.save()
            messages.success(request, "Image uploaded successfully.")
            return redirect("destination_detail", pk=destination.pk)
    else:
        form = DestinationImageForm()

    return render(
        request,
        "tour/upload_destination_image.html",
        {"form": form, "destination": destination},
    )
from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def upload_activity(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    booking = destination.booking  # get the related booking

    if request.method == "POST":
        form = ActivityForm(request.POST, booking=booking)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.destination = destination
            activity.save()
            form.save_m2m()  # save travelers
            messages.success(request, "Activity added successfully.")
            return redirect("booking_detail", pk=booking.id)
    else:
        form = ActivityForm(booking=booking)

    # ✅ Generate time slots (06:00 – 20:30 in 30-min steps)
    times = []
    start = datetime.strptime("06:00", "%H:%M")
    end = datetime.strptime("20:30", "%H:%M")
    step = timedelta(minutes=30)

    while start <= end:
        times.append(start.strftime("%H:%M"))
        start += step

    return render(
        request,
        "tour/upload_activity.html",
        {
            "form": form,
            "destination": destination,
            "time_slots": times,   # 👈 pass to template
        },
    )



@login_required
def upload_stay(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    booking = destination.booking  # ✅

    if request.method == "POST":
        form = StayForm(request.POST, booking=booking)  # ✅
        if form.is_valid():
            stay = form.save(commit=False)
            stay.destination = destination
            stay.save()
            form.save_m2m()  # ✅ travelers saved
            messages.success(request, "Stay added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = StayForm(initial={"destination": destination}, booking=booking)
        form.fields["destination"].widget = forms.HiddenInput()

    return render(request, "tour/upload_stay.html", {
        "form": form, "title": "Add Stay", "destination": destination
    })

@login_required
def upload_dining_expense(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    booking = destination.booking  # ✅

    if request.method == "POST":
        form = DiningExpenseForm(request.POST, booking=booking)  # ✅
        if form.is_valid():
            de = form.save(commit=False)
            de.destination = destination
            de.save()
            form.save_m2m()  # ✅ travelers saved
            messages.success(request, "Dining expense added.")
            return redirect("destination_detail", pk=destination.id)
    else:
        form = DiningExpenseForm(initial={"destination": destination}, booking=booking)
        form.fields["destination"].widget = forms.HiddenInput()

    return render(request, "tour/upload_dining.html", {
        "form": form, "title": "Add Dining Expense", "destination": destination
    })


@login_required
def upload_restaurant(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if request.method == "POST":
        form = RestaurantForm(request.POST, request.FILES)
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
        form = TravelLegForm(request.POST, booking=booking)  
        if form.is_valid():
            leg = form.save(commit=False)
            leg.booking = booking
            leg.save()
            form.save_m2m()  # ✅ travelers saved
            messages.success(request, "Travel leg added.")
            return redirect("booking_detail", pk=booking.id)
    else:
        form = TravelLegForm(initial={"booking": booking}, booking=booking)  
        form.fields["booking"].widget = forms.HiddenInput()

        # still keep your destination filters
        form.fields["from_destination"].queryset = booking.destinations.all()
        form.fields["to_destination"].queryset = booking.destinations.all()

    return render(request, "tour/upload_travel_leg.html", {
        "form": form, "title": "Add Travel Leg", "booking": booking
    })


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

from .models import Booking

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

from .models import Booking

from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
import tempfile

from .models import Booking

def booking_pdf(request, pk):
    booking = Booking.objects.get(pk=pk)
    travel_legs = booking.travel_legs.all()

    # Load the HTML template you wrote for the PDF
    template = get_template("tour/booking_pdf.html")
    html_string = template.render({
        "booking": booking,
        "travel_legs": travel_legs,
    })

    # Create a PDF
    with tempfile.NamedTemporaryFile(delete=True) as output:
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(output.name)
        output.seek(0)
        response = HttpResponse(output.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="Booking_{booking.id}.pdf"'
        return response



# views.py
@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "tour/profile.html", {"form": form, "profile": profile})



@login_required
def planner_list(request):
    """List all planners with latest subscription"""
    planners = Profile.objects.select_related("user").prefetch_related("subscriptions")
    return render(request, "tour/planner_list.html", {"planners": planners})


@login_required
def subscription_list(request, profile_id):
    """Show all subscriptions for a given planner"""
    profile = get_object_or_404(Profile, id=profile_id)
    subscriptions = profile.subscriptions.order_by("-start_date")
    return render(request, "tour/subscription_list.html", {"profile": profile, "subscriptions": subscriptions})



# ========================
# PayPal SDK Configuration
# ========================
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})


# ========================
# USER (Planner) VIEWS
# ========================

@login_required
def my_subscriptions(request):
    """Show logged-in planner’s subscriptions"""
    profile = request.user.profile
    subs = profile.subscriptions.all()
    return render(request, "subscriptions/my_subscriptions.html", {"subscriptions": subs})


@login_required
def my_subscription_create(request):
    """Planner creates a new subscription (pending until paid & admin-approved)"""
    profile = request.user.profile
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.profile = profile
            subscription.status = "Pending"
            subscription.payment_status = "pending"
            subscription.save()
            messages.success(request, "Subscription created. Please proceed with payment.")
            return redirect("create_payment", subscription_id=subscription.id)
    else:
        form = SubscriptionForm()
    return render(request, "subscriptions/my_subscription_form.html", {"form": form})


@login_required
def my_subscription_edit(request, pk):
    """Edit subscription before payment"""
    profile = request.user.profile
    subscription = get_object_or_404(Subscription, pk=pk, profile=profile, payment_status="pending")
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect("my_subscriptions")
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, "subscriptions/my_subscription_form.html", {"form": form})


# ========================
# PAYPAL VIEWS
# ========================

@login_required
def create_payment(request, subscription_id):
    """Start PayPal payment for subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, profile=request.user.profile)
    request.session["subscription_id"] = subscription.id

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse("execute_payment")),
            "cancel_url": request.build_absolute_uri(reverse("my_subscriptions")),
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": subscription.plan,
                    "sku": f"sub_{subscription.id}",
                    "price": str(subscription.fee),
                    "currency": "USD",   # ⚠️ update if supporting KES with conversion
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(subscription.fee),
                "currency": "USD"
            },
            "description": f"Subscription payment for {subscription.plan}"
        }]
    })

    if payment.create():
        subscription.transaction_id = payment.id
        subscription.save()
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        return render(request, "subscriptions/payment_error.html", {"error": payment.error})


@login_required
def execute_payment(request):
    """Finalize PayPal payment and mark subscription as paid (but still Pending until admin approves)"""
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        subscription_id = request.session.get("subscription_id")
        subscription = Subscription.objects.get(id=subscription_id)

        subscription.payment_status = "completed"
        subscription.save()

        messages.success(request, "Payment successful! Awaiting admin approval.")
        return render(request, "subscriptions/payment_success.html", {"subscription": subscription})
    else:
        return render(request, "subscriptions/payment_error.html", {"error": payment.error})


# ========================
# ADMIN VIEWS
# ========================

@staff_member_required
def admin_dashboard(request):
    """List planners with their latest subscription (staff-only)."""
    q = request.GET.get("q", "").strip()

    subs_prefetch = Prefetch('subscriptions', queryset=Subscription.objects.order_by('-start_date'))
    profiles_qs = Profile.objects.select_related('user').prefetch_related(subs_prefetch)

    if q:
        profiles_qs = profiles_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(company_name__icontains=q)
        )

    paginator = Paginator(profiles_qs, 25)
    page = request.GET.get('page')
    profiles = paginator.get_page(page)

    return render(request, "tour/admin_dashboard.html", {"profiles": profiles, "q": q})


@staff_member_required
def admin_planner_detail(request, profile_id):
    """Detail view of planner with subscriptions"""
    profile = get_object_or_404(Profile.objects.select_related('user').prefetch_related('subscriptions'), pk=profile_id)
    return render(request, "tour/admin_planner_detail.html", {"profile": profile})


@staff_member_required
def admin_subscription_edit(request, sub_id):
    """Admin edit/extend subscription"""
    subscription = get_object_or_404(Subscription, pk=sub_id)
    if request.method == "POST":
        form = AdminSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            extend_days = form.cleaned_data.get("extend_days") or 0
            sub = form.save(commit=False)
            if extend_days:
                sub.end_date = (sub.end_date or date.today()) + timedelta(days=extend_days)
            sub.save()
            messages.success(request, "Subscription updated.")
            return redirect("admin_dashboard")
    else:
        form = AdminSubscriptionForm(instance=subscription)
    return render(request, "tour/admin_subscription_edit.html", {"form": form, "subscription": subscription})


@staff_member_required
def admin_subscription_toggle(request, sub_id):
    """Admin approves / deactivates subscription"""
    subscription = get_object_or_404(Subscription, pk=sub_id)
    if request.method == "POST":
        if subscription.status == "Pending" and subscription.payment_status == "completed":
            # Approve subscription
            subscription.status = "Active"
            subscription.start_date = date.today()
            subscription.end_date = date.today() + timedelta(days=30)
        else:
            # Toggle deactivation
            subscription.status = "Expired"
        subscription.save()
        messages.success(request, f"Subscription status updated: {subscription.status}")
    return redirect("admin_dashboard")