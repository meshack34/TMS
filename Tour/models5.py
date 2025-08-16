# tour/models.py
from decimal import Decimal
from datetime import timedelta, date
from django.contrib.auth.models import User
from django.db import models

class Client(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.full_name


# ------------------------
# DESTINATION MANAGEMENT
# ------------------------

class Destination(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='destinations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='destinations')
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    description = models.TextField()
    map_embed_code = models.TextField(help_text="Embed iframe from Google Maps")

    def get_valid_dates(self):
        """Return all valid dates within the related date ranges."""
        valid_dates = []
        for date_range in self.date_ranges.all():
            current = date_range.start_date
            while current <= date_range.end_date:
                valid_dates.append(current)
                current += timedelta(days=1)
        return valid_dates

    def __str__(self):
        return self.name


class DateRange(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='date_ranges')
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.destination.name}: {self.start_date} to {self.end_date}"


class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='destination_gallery/')

    def __str__(self):
        return f"Image for {self.destination.name}"


class Room(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='rooms/')
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost per night in KSh")
    basis = models.CharField(max_length=50, help_text="e.g., FB, HB, BB")
    nights = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class Restaurant(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='restaurants/')

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class Activity(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.title} on {self.date} from {self.start_time} to {self.end_time}"


class Information(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='info')
    content = models.TextField()

    def __str__(self):
        return f"Info for {self.destination.name}"


# ------------------------
# TRANSPORT MANAGEMENT
# ------------------------
class TravelLeg(models.Model):
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)
    date = models.DateField()
    pick_up = models.CharField(max_length=255)
    drop_off = models.CharField(max_length=255)
    transport_name = models.CharField(max_length=255, blank=True, null=True, help_text="Flight or bus name")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    from_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='departures'
    )
    to_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='arrivals'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_booking_type_display()} {self.pick_up} → {self.drop_off} ({self.booking})"

class TravelLeg(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('transfer', 'Transfer'),
        ('bus', 'bus'),
        ('train', 'train'),
    ]
    
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    mode = models.CharField(max_length=100)  # e.g., flight, bus, train
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='travel_legs', null=True, blank=True)
    planner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='planned_travel_legs')
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)
    date = models.DateField()
    pick_up = models.CharField(max_length=255)
    drop_off = models.CharField(max_length=255)
    transport_name = models.CharField(max_length=255, blank=True, null=True, help_text="Flight or bus name")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    from_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='departures'
    )
    to_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='arrivals'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_booking_type_display()} {self.pick_up} → {self.drop_off} on {self.date}"


# ------------------------
# BOOKING MANAGEMENT
# ------------------------
from django.db import models
from django.utils import timezone
from django.db.models import Sum


class Client(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.full_name


class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking #{self.id} - {self.client.full_name}"

    def get_total_cost(self):
        """Sum costs from all related destinations, rooms, activities, and travel legs."""
        destinations_cost = self.destinations.aggregate(total=Sum('cost'))['total'] or 0
        travel_cost = self.travel_legs.aggregate(total=Sum('cost'))['total'] or 0
        return destinations_cost + travel_cost

    def get_summary(self):
        """Returns a structured summary for easy use in views/templates."""
        return {
            "client": self.client.full_name,
            "dates": f"{self.start_date} → {self.end_date}",
            "total_cost": self.get_total_cost(),
            "destinations": [
                {
                    "name": dest.name,
                    "start": dest.start_date,
                    "end": dest.end_date,
                    "cost": dest.cost,
                    "activities": [act.name for act in dest.activities.all()],
                }
                for dest in self.destinations.all()
            ],
            "travel_legs": [
                {
                    "from": leg.origin,
                    "to": leg.destination,
                    "mode": leg.mode,
                    "cost": leg.cost
                }
                for leg in self.travel_legs.all()
            ]
        }


class Destination(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='destinations')
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.booking.client.full_name})"


class Activity(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=255)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.name} - {self.destination.name}"


class TravelLeg(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='travel_legs')
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    mode = models.CharField(max_length=100)  # e.g., flight, bus, train
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.mode})"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    first_name = models.CharField(max_length=100, default='Unknown')
    last_name = models.CharField(max_length=100, default='Unknown')
    email = models.EmailField(max_length=100, default='default@example.com')
    phone = models.CharField(max_length=100, default='0000000000')
    origin_location = models.CharField(max_length=100, default='Unknown')
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    departure_date = models.DateField(default='2025-01-01')
    return_date = models.DateField(default='2025-01-01')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ------------------------
# ITINERARY MANAGEMENT
# ------------------------

class Itinerary(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='itineraries')
    location = models.CharField(max_length=100, default='Unknown')
    activity = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default='2025-01-01')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    planner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='planned_itineraries')
    class Meta:
        ordering = ['updated_at', '-created_at']

    def __str__(self):
        return f"Itinerary for {self.booking} - {self.location}"
   
