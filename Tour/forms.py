from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import (
    Client, Booking, Destination, Activity, Stay, DiningExpense, TravelLeg, Restaurant
)


class PlannerCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        user.is_staff = True
        if commit:
            user.save()
        return user


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email", "phone"]


class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        exclude = ["booking"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "map_embed_code": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Paste Google Maps iframe embed code here"
            }),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date.")
        if self.booking and start and end:
            if start < self.booking.start_date or end > self.booking.end_date:
                raise forms.ValidationError(
                    f"Destination dates must be within the booking window "
                    f"({self.booking.start_date} → {self.booking.end_date})."
                )
        return cleaned


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["client", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["destination", "name", "date", "start_time", "end_time", "cost"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


class StayForm(forms.ModelForm):
    class Meta:
        model = Stay
        fields = ["destination", "hotel_name", "nightly_rate", "nights", "rooms", "basis"]


class DiningExpenseForm(forms.ModelForm):
    class Meta:
        model = DiningExpense
        fields = ["destination", "restaurant", "date", "description", "cost"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ["destination", "name"]


class TravelLegForm(forms.ModelForm):
    class Meta:
        model = TravelLeg
        fields = [
            "booking",
            "mode",
            "date",
            "from_location",
            "to_location",
            "from_destination",
            "to_destination",
            "cost",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
