from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User



class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Extra details
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)

    # Travel preferences
    dietary_preferences = models.TextField(blank=True, null=True)  # e.g. vegetarian
    medical_notes = models.TextField(blank=True, null=True)        # e.g. allergies
    preferred_language = models.CharField(max_length=50, blank=True, null=True)
    special_requests = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# auto-create Profile when new User is created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # ensure a profile exists, then save
        profile, _ = Profile.objects.get_or_create(user=instance)
        profile.save()


class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking #{self.id} - {self.client.first_name} {self.client.last_name}"

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


class Traveler(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="travelers")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    relation = models.CharField(max_length=50, blank=True, null=True)  # e.g. child, spouse

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.booking})"

class Destination(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="destinations")
    country = models.CharField(max_length=100)
    description = models.TextField()
    map_embed_code = models.TextField(help_text="Embed iframe from Google Maps")
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.booking.client.first_name} {self.booking.client.last_name})"


class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='galleries')
    image = models.ImageField(upload_to='destination_gallery/')

    def __str__(self):
        return f"Image for {self.destination.name}"


class Stay(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="stays")
    hotel_name = models.CharField(max_length=255)
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    nights = models.PositiveIntegerField()
    rooms = models.PositiveIntegerField(default=1)
    basis = models.CharField(max_length=50, choices=[("BB", "Bed & Breakfast"), ("HB", "Half Board"), ("FB", "Full Board"), ("AI", "All Inclusive")])
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    travelers = models.ManyToManyField("Traveler", related_name="stays", blank=True)

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
    travelers = models.ManyToManyField("Traveler", related_name="activities", blank=True)


    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class Restaurant(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="restaurants")
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='restaurants/')
    description = models.TextField()
    

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class DiningExpense(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="dining_expenses")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    travelers = models.ManyToManyField("Traveler", related_name="dining_expenses", blank=True)
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
    travelers = models.ManyToManyField("Traveler", related_name="travel_legs", blank=True)

    def __str__(self):
        return f"{self.mode} {self.from_location} → {self.to_location} ({self.booking.client.first_name} {self.booking.client.last_name})"



class Subscription(models.Model):
    PLAN_CHOICES = [
        ("basic", "Basic"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),     # Planner created, waiting admin approval
        ("Active", "Active"),       # Approved & running
        ("Expired", "Expired"),     # End date passed
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES)
    fee = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # PayPal tracking
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(
        max_length=50,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")],
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile', 'start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['transaction_id']),
        ]
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.profile.user.username} - {self.plan} ({self.status}/{self.payment_status})"

    @property
    def is_expired(self):
        return self.end_date and self.end_date < timezone.now().date()

    def activate(self, months=1):
        """Admin approves & activates subscription"""
        self.status = "Active"
        self.start_date = timezone.now().date()
        self.end_date = self.start_date + timezone.timedelta(days=30 * months)
        self.save()