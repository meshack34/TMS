from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking, Activity, Stay, DiningExpense
from .forms import (  # note: file name is form.py as you asked
    BookingForm,
    DestinationFormSet,
    ActivityFormSet,
    StayFormSet,
    DiningExpenseFormSet,
    TravelLegFormSet,
)
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import RegisterForm

def register_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            messages.success(request, "Planner account created successfully.")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')



def planner(request, pk=None):
    """
    One-page planner. Create a new booking or edit an existing one.
    - Booking form
    - Destinations (inline formset)
    - Activities / Stays / Dining (model formsets with destination selector)
    - Travel legs (inline formset)
    """
    creating = pk is None
    booking = None
    if not creating:
        booking = get_object_or_404(Booking, pk=pk)

    if request.method == "POST":
        # Always bind the booking form first
        booking_form = BookingForm(request.POST, instance=booking)

        # We need a booking instance for inline formsets; save early in a transaction if creating
        with transaction.atomic():
            if booking_form.is_valid():
                booking = booking_form.save()

                # DESTINATIONS (inline)
                dest_formset = DestinationFormSet(
                    request.POST, instance=booking, prefix="dest"
                )

                # Destination queryset for the 3 child model-formsets
                dest_qs = booking.destinations.all()

                # ACTIVITIES / STAYS / DINING (model formsets scoped to this booking's destinations)
                activity_formset = ActivityFormSet(
                    request.POST,
                    prefix="act",
                    queryset=Activity.objects.filter(destination__booking=booking),
                    form_kwargs={"dest_qs": dest_qs},
                )
                stay_formset = StayFormSet(
                    request.POST,
                    prefix="stay",
                    queryset=Stay.objects.filter(destination__booking=booking),
                    form_kwargs={"dest_qs": dest_qs},
                )
                dining_formset = DiningExpenseFormSet(
                    request.POST,
                    prefix="dine",
                    queryset=DiningExpense.objects.filter(destination__booking=booking),
                    form_kwargs={"dest_qs": dest_qs},
                )

                # TRAVEL LEGS (inline)
                travel_formset = TravelLegFormSet(
                    request.POST, instance=booking, prefix="travel"
                )

                # Validate everything
                all_valid = (
                    dest_formset.is_valid()
                    and activity_formset.is_valid()
                    and stay_formset.is_valid()
                    and dining_formset.is_valid()
                    and travel_formset.is_valid()
                )

                if all_valid:
                    # Save destinations first (so destination ids exist for children)
                    dest_formset.save()

                    # Re-scope after potential new destinations saved
                    dest_qs = booking.destinations.all()
                    for fs in (activity_formset, stay_formset, dining_formset):
                        for form in fs.forms:
                            if "destination" in form.fields:
                                form.fields["destination"].queryset = dest_qs

                    # Save children & travel legs
                    activity_formset.save()
                    stay_formset.save()
                    dining_formset.save()
                    travel_formset.save()

                    messages.success(request, "Booking saved successfully.")
                    return redirect("planner", pk=booking.pk)
                else:
                    messages.error(request, "Please correct the errors below.")
            else:
                # invalid booking form
                dest_formset = DestinationFormSet(prefix="dest")
                activity_formset = ActivityFormSet(
                    prefix="act", queryset=Activity.objects.none(), form_kwargs={"dest_qs": None}
                )
                stay_formset = StayFormSet(
                    prefix="stay", queryset=Stay.objects.none(), form_kwargs={"dest_qs": None}
                )
                dining_formset = DiningExpenseFormSet(
                    prefix="dine", queryset=DiningExpense.objects.none(), form_kwargs={"dest_qs": None}
                )
                travel_formset = TravelLegFormSet(prefix="travel")

    else:
        # GET
        booking_form = BookingForm(instance=booking)

        if booking:
            dest_formset = DestinationFormSet(instance=booking, prefix="dest")
            dest_qs = booking.destinations.all()

            activity_formset = ActivityFormSet(
                prefix="act",
                queryset=Activity.objects.filter(destination__booking=booking),
                form_kwargs={"dest_qs": dest_qs},
            )
            stay_formset = StayFormSet(
                prefix="stay",
                queryset=Stay.objects.filter(destination__booking=booking),
                form_kwargs={"dest_qs": dest_qs},
            )
            dining_formset = DiningExpenseFormSet(
                prefix="dine",
                queryset=DiningExpense.objects.filter(destination__booking=booking),
                form_kwargs={"dest_qs": dest_qs},
            )
            travel_formset = TravelLegFormSet(instance=booking, prefix="travel")
        else:
            # New booking: nothing yet, empty sets
            dest_formset = DestinationFormSet(prefix="dest")
            activity_formset = ActivityFormSet(
                prefix="act", queryset=Activity.objects.none(), form_kwargs={"dest_qs": None}
            )
            stay_formset = StayFormSet(
                prefix="stay", queryset=Stay.objects.none(), form_kwargs={"dest_qs": None}
            )
            dining_formset = DiningExpenseFormSet(
                prefix="dine", queryset=DiningExpense.objects.none(), form_kwargs={"dest_qs": None}
            )
            travel_formset = TravelLegFormSet(prefix="travel")

    # Compute totals if we have a booking instance
    totals = None
    if booking:
        totals = {
            "accommodation": booking.accommodation_total(),
            "activities": booking.activities_total(),
            "dining": booking.dining_total(),
            "transport": booking.transport_total(),
            "subtotal": booking.subtotal(),
            "grand_total": booking.grand_total(),
        }

    return render(
        request,
        "planner.html",
        {
            "creating": creating,
            "booking": booking,
            "booking_form": booking_form,
            "dest_formset": dest_formset,
            "activity_formset": activity_formset,
            "stay_formset": stay_formset,
            "dining_formset": dining_formset,
            "travel_formset": travel_formset,
            "totals": totals,
        },
    )
