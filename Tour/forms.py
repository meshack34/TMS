from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Subscription
from .models import Traveler
from .models import Subscription

from .models import (
    Client, Booking, Destination,DestinationImage, Activity, Stay, DiningExpense, TravelLeg, Restaurant
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
        fields = [
            "first_name", "last_name", "email", "phone_number",
            "date_of_birth", "nationality", "passport_number", "passport_expiry",
            "address", "emergency_contact_name", "emergency_contact_phone",
            "dietary_preferences", "medical_notes", "preferred_language",
            "special_requests",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "passport_expiry": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "address": forms.Textarea(attrs={"rows": 2, "class": "form-control form-control-sm"}),
            "medical_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control form-control-sm"}),
            "special_requests": forms.Textarea(attrs={"rows": 2, "class": "form-control form-control-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = existing_classes + " form-control form-control-sm"



class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["client", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


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



class DestinationImageForm(forms.ModelForm):
    class Meta:
        model = DestinationImage
        fields = ["image"]



 
class StayForm(forms.ModelForm):
    class Meta:
        model = Stay
        fields = ["destination", "hotel_name", "nightly_rate", "nights", "rooms", "basis", "travelers"]

    travelers = forms.ModelMultipleChoiceField(
        queryset=Traveler.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        if booking:
            # limit travelers to those in this booking
            self.fields["travelers"].queryset = booking.travelers.all()

class DiningExpenseForm(forms.ModelForm):
    class Meta:
        model = DiningExpense
        fields = ["destination", "restaurant", "date", "description", "cost", "travelers"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    travelers = forms.ModelMultipleChoiceField(
        queryset=Traveler.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        if booking:
            self.fields["travelers"].queryset = booking.travelers.all()

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["destination", "name", "date", "start_time", "end_time", "cost", "travelers"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    travelers = forms.ModelMultipleChoiceField(
        queryset=Traveler.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        if booking:
            self.fields["travelers"].queryset = booking.travelers.all()



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
            "travelers",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    travelers = forms.ModelMultipleChoiceField(
        queryset=Traveler.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        if booking:
            self.fields["travelers"].queryset = booking.travelers.all()




class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ["destination", "name", "image", "description"]



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_picture", "phone", "company_name"]



class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["plan", "fee", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }



class TravelerForm(forms.ModelForm):
    class Meta:
        model = Traveler
        fields = ["first_name", "last_name", "age", "relation"]


class AdminSubscriptionForm(forms.ModelForm):
    extend_days = forms.IntegerField(
        required=False,
        min_value=1,
        help_text="Add days to end date",
        label="Extend by (days)"
    )

    class Meta:
        model = Subscription
        fields = ['plan', 'fee', 'end_date', 'status', 'payment_status', 'transaction_id']