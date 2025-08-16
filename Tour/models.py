from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking #{self.id} - {self.client.name}"

    # ===== COST AGGREGATION METHODS =====
    def accommodation_total(self):
        return sum((stay.total_cost or Decimal("0.00")) for dest in self.destinations.all() for stay in dest.stays.all())

    def activities_total(self):
        return sum((act.cost or Decimal("0.00")) for dest in self.destinations.all() for act in dest.activities.all())

    def dining_total(self):
        return sum((dining.cost or Decimal("0.00")) for dest in self.destinations.all() for dining in dest.dining_expenses.all())

    def transport_total(self):
        return sum((leg.cost or Decimal("0.00")) for leg in self.travel_legs.all())

    def subtotal(self):
        return self.accommodation_total() + self.activities_total() + self.dining_total() + self.transport_total()

    def grand_total(self):
        return self.subtotal()  # You can add taxes/fees here later if needed

    def cost_breakdown(self):
        return {
            "Accommodation": self.accommodation_total(),
            "Activities": self.activities_total(),
            "Dining": self.dining_total(),
            "Transport": self.transport_total(),
            "Total": self.grand_total(),
        }


class Destination(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="destinations")
    country = models.CharField(max_length=100)
    description = models.TextField()
    map_embed_code = models.TextField(help_text="Embed iframe from Google Maps")
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.booking.client.name})"


class Stay(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="stays")
    hotel_name = models.CharField(max_length=255)
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    nights = models.PositiveIntegerField()
    rooms = models.PositiveIntegerField(default=1)
    basis = models.CharField(max_length=50, choices=[("BB", "Bed & Breakfast"), ("HB", "Half Board"), ("FB", "Full Board"), ("AI", "All Inclusive")])
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_cost = Decimal(self.nightly_rate) * self.nights * self.rooms
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hotel_name} ({self.destination.name})"


class Activity(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="activities")
    name = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class Restaurant(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="restaurants")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class DiningExpense(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="dining_expenses")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Dining - {self.restaurant.name if self.restaurant else 'Other'} ({self.destination.name})"


class TravelLeg(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="travel_legs")
    mode = models.CharField(max_length=50, choices=[("Flight", "Flight"), ("Train", "Train"), ("Bus", "Bus"), ("Car", "Car Rental"), ("Boat", "Boat")])
    date = models.DateField()
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    from_destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="departing_legs")
    to_destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="arriving_legs")
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    def __str__(self):
        return f"{self.mode} {self.from_location} → {self.to_location} ({self.booking.client.name})"
