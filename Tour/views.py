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
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Client
from .forms import ClientForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.lib.pagesizes import A4
import os
from .models import (
    Client, Booking, Destination,DestinationImage, Activity, Stay, DiningExpense, TravelLeg, Restaurant
)
from .forms import (
    PlannerCreationForm,ProfileForm,
    ClientForm, BookingForm, DestinationForm, DestinationImageForm,
    ActivityForm, StayForm, DiningExpenseForm, RestaurantForm, TravelLegForm
)

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
                Prefetch("travel_legs", queryset=TravelLeg.objects.select_related("from_destination", "to_destination"))
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        booking: Booking = ctx["booking"]

        # existing
        ctx["costs"] = booking.cost_breakdown()
        ctx["destinations"] = booking.destinations.all().order_by("start_date")

        # NEW: ordered legs + summary
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
            "by_mode": by_mode,  # dict like {"Flight": 123.45, ...}
        }
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
                Prefetch("galleries", queryset=DestinationImage.objects.all()),
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


@login_required
def booking_pdf(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # PDF Response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="booking_{pk}.pdf"'

    # Document setup
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", fontSize=18, alignment=1, spaceAfter=20, textColor=colors.HexColor("#0056A6")))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=13, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor("#333333"), underlineWidth=0.5))
    styles.add(ParagraphStyle(name="NormalText", fontSize=10, leading=14, spaceAfter=6))

    elements = []

    # ---------------- HEADER ----------------
    elements.append(Paragraph("Tour Travel Management System", styles["Title"]))
    elements.append(Paragraph(f"Booking Report", styles["CenterTitle"]))

    client_name = f"{booking.client.first_name} {booking.client.last_name}"
    elements.append(Paragraph(f"Client: <b>{client_name}</b>", styles["NormalText"]))
    elements.append(Paragraph(f"Booking ID: <b>{booking.pk}</b>", styles["NormalText"]))

    # ---------------- SUMMARY ----------------
    # Booking Info
    info_data = [
        ["Client:", client_name],
        ["Start Date:", str(booking.start_date)],
        ["End Date:", str(booking.end_date)],
    ]
    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(Paragraph("Booking Information", styles["SectionHeading"]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Cost Breakdown
    breakdown = booking.cost_breakdown()
    cost_data = [["Category", "Cost (KSH)"]]
    for k, v in breakdown.items():
        cost_data.append([k, f"{v:,.2f}"])  # formatted with commas
    cost_table = Table(cost_data, colWidths=[200, 150])
    cost_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056A6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(Paragraph("Cost Breakdown", styles["SectionHeading"]))
    elements.append(cost_table)
    elements.append(Spacer(1, 15))

    # Travel Itinerary
    legs = booking.travel_legs.all()
    if legs:
        travel_data = [["Date", "Mode", "From", "To", "Cost (KSH)"]]
        for leg in legs:
            travel_data.append([
                str(leg.date),
                leg.mode,
                str(leg.from_destination or leg.from_location),
                str(leg.to_destination or leg.to_location),
                f"{leg.cost:,.2f}",  # formatted with commas
            ])
        travel_table = Table(travel_data, colWidths=[70, 70, 120, 120, 70])
        travel_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#444444")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(Paragraph("Travel Itinerary", styles["SectionHeading"]))
        elements.append(travel_table)
        elements.append(Spacer(1, 15))

    # ---------------- FULL-PAGE IMAGES ----------------
    elements.append(PageBreak())
    elements.append(Paragraph("Destinations & Restaurants", styles["SectionHeading"]))

    max_width, max_height = A4[0] - 80, A4[1] - 80  # fit inside margins

    # Destinations
    for d in booking.destinations.all():
        for g in d.galleries.all():
            if g.image and os.path.exists(g.image.path):
                try:
                    elements.append(PageBreak())
                    elements.append(Paragraph(f"Destination: {d.name}", styles["CenterTitle"]))
                    img = RLImage(g.image.path)
                    img._restrictSize(max_width, max_height)
                    elements.append(img)
                except Exception:
                    pass

    # Restaurants
    for d in booking.destinations.all():
        for r in d.restaurants.all():
            if r.image and os.path.exists(r.image.path):
                try:
                    elements.append(PageBreak())
                    elements.append(Paragraph(f"Restaurant: {r.name}", styles["CenterTitle"]))
                    img = RLImage(r.image.path)
                    img._restrictSize(max_width, max_height)
                    elements.append(img)
                except Exception:
                    pass

    # ---------------- FOOTER ----------------
    elements.append(PageBreak())
    elements.append(Paragraph("<i>Generated by Tour Travel Management System © 2025</i>", styles["NormalText"]))

    # Build PDF
    doc.build(elements)
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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Subscription
from .forms import SubscriptionForm

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


@login_required
def subscription_create(request, profile_id):
    """Add a new subscription to a planner"""
    profile = get_object_or_404(Profile, id=profile_id)

    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.profile = profile
            subscription.save()
            messages.success(request, "Subscription created successfully.")
            return redirect("subscription_list", profile_id=profile.id)
    else:
        form = SubscriptionForm()

    return render(request, "tour/subscription_form.html", {"form": form, "profile": profile})


@login_required
def subscription_edit(request, pk):
    """Edit an existing subscription"""
    subscription = get_object_or_404(Subscription, pk=pk)

    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated successfully.")
            return redirect("subscription_list", profile_id=subscription.profile.id)
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, "tour/subscription_form.html", {"form": form, "profile": subscription.profile})

import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Profile, Subscription

# Existing views like planner_list(), subscription_list() remain the same


@login_required
def subscription_checkout(request, profile_id, plan):
    """Show PayPal checkout for a selected plan"""
    profile = get_object_or_404(Profile, id=profile_id)

    fees = {"basic": 500, "pro": 1500, "enterprise": 5000}  # KSH example
    if plan not in fees:
        messages.error(request, "Invalid plan selected.")
        return redirect("planner_list")

    fee = fees[plan]

    # Create subscription (pending)
    subscription = Subscription.objects.create(
        profile=profile,
        plan=plan,
        fee=fee,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + datetime.timedelta(days=30),
        is_active=False,
        payment_status="pending",
    )

    context = {
        "profile": profile,
        "subscription": subscription,
        "paypal_client_id": "YOUR_PAYPAL_CLIENT_ID",  # replace with real one
    }
    return render(request, "tour/subscription_checkout.html", context)


@login_required
def subscription_success(request, sub_id):
    """Mark subscription as active after successful PayPal payment"""
    subscription = get_object_or_404(Subscription, id=sub_id)
    subscription.is_active = True
    subscription.payment_status = "completed"
    subscription.save()

    messages.success(request, f"Payment successful! {subscription.plan} subscription activated.")
    return redirect("subscription_list", profile_id=subscription.profile.id)


@login_required
def subscription_cancel(request, sub_id):
    """Handle canceled PayPal payment"""
    subscription = get_object_or_404(Subscription, id=sub_id)
    subscription.payment_status = "failed"
    subscription.save()

    messages.error(request, "Payment was canceled.")
    return redirect("subscription_list", profile_id=subscription.profile.id)
