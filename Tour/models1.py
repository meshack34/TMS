#tour/models
from django.contrib.auth.models import User
from django.db import models
from datetime import date
from django.db import models
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class Destination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='destinations')
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    description = models.TextField()
    map_embed_code = models.TextField(help_text="Embed iframe from Google Maps")

    def get_valid_dates(self):
        from datetime import timedelta
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



class TravelLeg(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('transfer', 'Transfer'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_legs')
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)
    date = models.DateField()
    pick_up = models.CharField(max_length=255)
    drop_off = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # optional links to destinations (can be null)
    from_destination = models.ForeignKey('Destination', on_delete=models.SET_NULL, null=True, blank=True, related_name='departures')
    to_destination = models.ForeignKey('Destination', on_delete=models.SET_NULL, null=True, blank=True, related_name='arrivals')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_booking_type_display()} {self.pick_up} → {self.drop_off} on {self.date}"


class Booking(models.Model):
    first_name=models.CharField(max_length=100,default='Unknown')
    last_name=models.CharField(max_length=100,  default='Unknown')
    email=models.EmailField(max_length=100, default='default@example.com')
    phone=models.CharField(max_length=100,  default='0000000000')
    Original_location=models.CharField(max_length=100, default='Unknown')
    destination=models.CharField(max_length=100, default='Unknown')
    departure_date=models.DateField(default='2025-01-01')
    return_date=models.DateField(default='2025-01-01')
    created_at= models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at= models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering= ['-updated_at', '-created_at']

    def __str__(self):
        return self.first_name + ' ' + self.last_name 
    



class Itinerary(models.Model):
    first_name=models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    location=models.CharField(max_length=100, default='Unknown')
    activity=models.TextField()
    cost=models.DecimalField(max_digits=10, decimal_places=2 ) 
    date=models.DateField(default='2025-01-01')
   # time=models.TimeField()  
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering= ['updated_at','-created_at']
    

    def __str__(self):
        return self.location




