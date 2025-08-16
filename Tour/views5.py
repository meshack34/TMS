from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Booking,Itinerary
from .forms import BookingForm,ItineraryForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from .forms import DateRangeForm

#tour/views
from django.contrib.auth.decorators import login_required
from .models import Destination
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm, DestinationForm 
from .forms import ActivityForm, InformationForm
from .forms import DestinationImageForm, RoomForm, RestaurantForm
from .models import Destination
from django.http import JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import openpyxl
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Destination, Room, DateRange
from datetime import datetime
from django.db.models import Q  
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect
from datetime import timedelta


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist")
            return render(request, 'tour/login_register.html', {'page': page})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Username or Password is incorrect")    

    return render(request, 'tour/login_register.html', {'page': page})


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    form=UserCreationForm()
    if request.method=='POST':
        form=UserCreationForm(request.POST)
        if form.is_valid():
            user=form.save(commit=False)
            user.username=user.username.lower()
            user.save()
            messages.success(request,"User account created successfully")
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request,"An error occured during registration")


    context={'form':form}
    return render(request,'tour/login_register.html',context)

def logout_view(request):
    logout(request)
    return redirect('home') 


# @login_required
def add_destination_view(request):
    DateRangeFormSet = modelformset_factory(DateRange, form=DateRangeForm, extra=1)

    if request.method == 'POST':
        form = DestinationForm(request.POST)
        formset = DateRangeFormSet(request.POST, queryset=DateRange.objects.none())
        
        if form.is_valid() and formset.is_valid():
            dest = form.save(commit=False)
            dest.user = request.user
            dest.save()

            for subform in formset:
                if subform.cleaned_data:
                    date_range = subform.save(commit=False)
                    date_range.destination = dest
                    date_range.save()

            return redirect('dashboard')
    else:
        form = DestinationForm()
        formset = DateRangeFormSet(queryset=DateRange.objects.none())

    return render(request, 'tour/add_destination.html', {
        'form': form,
        'date_formset': formset,
    })


def destination_detail(request, id):
    destination = get_object_or_404(Destination, id=id)
    days = []

    for date_range in destination.date_ranges.all():
        current = date_range.start_date
        while current <= date_range.end_date:
            day_activities = destination.activities.filter(date=current).order_by('start_time')
            days.append({
                'date': current,
                'activities': day_activities
            })
            current += timedelta(days=1)

    tab_labels = ['Gallery', 'Rooms', 'Restaurants', 'Activities and Services', 'Information', 'Map']
    return render(request, 'tour/destination_detail.html', {
        'destination': destination,
        'tab_labels': tab_labels,
        'itinerary_days': days,
    })



@login_required
def dashboard_view(request):
    destinations = request.user.destinations.all()
    return render(request, 'tour/dashboardm.html', {'destinations': destinations})



def all_destinations(request):
    destinations = Destination.objects.all()
    return render(request, 'tour/all_destinations.html', {'destinations': destinations})

def homepage(request):
    featured_destinations = Destination.objects.all()[:2]
    context = {
        'featured_destinations': featured_destinations
    }
    return render(request, 'tour/home.html', context)


def destination_list(request):
    destinations = Destination.objects.all()
    return render(request, 'tour/destination_list.html', {'destinations': destinations})



@login_required
def upload_images(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)

    if request.method == 'POST':
        img_form = DestinationImageForm(request.POST, request.FILES)
        if img_form.is_valid():
            image = img_form.save(commit=False)
            image.destination = destination
            image.save()
            return redirect('destination_detail', id=destination.id)
    else:
        img_form = DestinationImageForm()
    
    return render(request, 'tour/upload_image.html', {'form': img_form, 'destination': destination})

@login_required
def upload_gallery_image(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)
    if request.method == 'POST':
        form = DestinationImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.destination = destination
            image.save()
            return redirect('destination_detail', id=destination.id)
    else:
        form = DestinationImageForm()
    return render(request, 'tour/upload_image.html', {'form': form, 'title': 'Upload Gallery Image'})

@login_required
def upload_room(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.destination = destination
            room.save()
            return redirect('destination_detail', id=destination.id)
    else:
        form = RoomForm()
    return render(request, 'tour/upload_room.html', {'form': form, 'title': 'Add Room'})

@login_required
def upload_restaurant(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.destination = destination
            restaurant.save()
            return redirect('destination_detail', id=destination.id)
    else:
        form = RestaurantForm()
    return render(request, 'tour/upload_image.html', {'form': form, 'title': 'Add Restaurant'})

@login_required
def edit_destination(request, id):
    destination = get_object_or_404(Destination, id=id, user=request.user)
    if request.method == 'POST':
        form = DestinationForm(request.POST, instance=destination)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = DestinationForm(instance=destination)
    return render(request, 'tour/edit_destination.html', {'form': form, 'destination': destination})

@login_required
def delete_destination(request, id):
    destination = get_object_or_404(Destination, id=id, user=request.user)
    if request.method == 'POST':
        destination.delete()
        return redirect('dashboard')
    return render(request, 'tour/delete_destination.html', {'destination': destination})




@login_required
def upload_activity(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.destination = destination
            activity.save()
            return redirect('destination_detail', id=destination.id)
    else:
        form = ActivityForm()

    return render(request, 'tour/upload_activity.html', {
        'form': form,
        'title': 'Add Activity',
        'destination': destination,
    })


       
@login_required
def upload_information(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id, user=request.user)
    if request.method == 'POST':
        form = InformationForm(request.POST)
        if form.is_valid():
            info = form.save(commit=False)
            info.destination = destination
            info.save()
            return redirect('destination_detail', id=destination.id)
    else:
        form = InformationForm()
    return render(request, 'tour/upload_information.html', {'form': form, 'title': 'Add Info', 'destination': destination})




@login_required
def accommodation_summary_view(request):
    client = request.user

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Parse the date strings if they exist
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    # Get all destinations for the client
    destinations = Destination.objects.filter(user=client).prefetch_related('rooms', 'daterange_set')

    summary = []
    grand_total = 0

    for destination in destinations:
        # Filter date ranges based on input (if any)
        date_ranges = destination.daterange_set.all()
        if start_date:
            date_ranges = date_ranges.filter(end_date__gte=start_date)
        if end_date:
            date_ranges = date_ranges.filter(start_date__lte=end_date)

        for date_range in date_ranges:
            destination_total = 0
            for room in destination.rooms.all():
                room_cost = room.cost * room.nights
                summary.append({
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date,
                    'destination': destination.name,
                    'accommodation': room.name,
                    'basis': room.basis,
                    'nights': room.nights,
                    'cost': room.cost,
                    'total_cost': room_cost,
                })
                destination_total += room_cost
            grand_total += destination_total

    return render(request, 'tour/accommodation_summary.html', {
        'summary': summary,
        'grand_total': grand_total,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })





from django.shortcuts import render
from .models import Destination
from datetime import timedelta
from django.db.models import Sum
def public_dashboard_view(request):
    destinations = Destination.objects.all().prefetch_related('rooms', 'date_ranges', 'activities')[:2]

    for dest in destinations:
        days = []
        for date_range in dest.date_ranges.all():
            current = date_range.start_date
            while current <= date_range.end_date:
                activities = dest.activities.filter(date=current)
                days.append({'date': current, 'activities': activities})
                current += timedelta(days=1)
        dest.itinerary_days = days
        totals = dest.rooms.aggregate(
            total_nights=Sum('nights'),
            total_cost=Sum('cost')
        )
        dest.total_nights = totals['total_nights'] or 0
        dest.total_cost = totals['total_cost'] or 0

    summary = get_accommodation_summary(destinations)
    return render(request, 'tour/public_dashboard.html', {
        'destinations': destinations,
        'summary': summary,
    })



def get_travel_dates(request, destination_id):
    date_ranges = DateRange.objects.filter(destination_id=destination_id)
    dates = []

    for dr in date_ranges:
        current = dr.start_date
        while current <= dr.end_date:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

    return JsonResponse({'dates': dates})



# tour/views.py  (only add/replace relevant functions below)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from .models import Destination, DateRange, Room, Activity
from datetime import datetime, timedelta
import openpyxl
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO

# reuse/definition
def get_accommodation_summary(destinations, start_date=None, end_date=None):
    summary = []
    for destination in destinations:
        date_ranges = destination.date_ranges.all()
        if start_date:
            date_ranges = date_ranges.filter(end_date__gte=start_date)
        if end_date:
            date_ranges = date_ranges.filter(start_date__lte=end_date)
        for date_range in date_ranges:
            for room in destination.rooms.all():
                total_cost = float(room.cost) * int(room.nights)
                summary.append({
                    'start_date': date_range.start_date,
                    'end_date': date_range.end_date,
                    'destination': destination.name,
                    'accommodation': room.name,
                    'basis': room.basis,
                    'nights': room.nights,
                    'cost': float(room.cost),
                    'total_cost': total_cost,
                })
    return summary

@login_required
def client_summary_viewm(request):
    user = request.user
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    destinations = Destination.objects.filter(user=user).prefetch_related(
        'rooms', 'date_ranges', 'images', 'activities', 'restaurants', 'info'
    )

    accommodation = get_accommodation_summary(destinations, start_date=start_date, end_date=end_date)

    # Example transport extraction using Activity model:
    flights = []
    transfers = []
    for dest in destinations:
        for act in dest.activities.all().order_by('date', 'start_time'):
            title = (act.title or "").lower()
            if "flight" in title:
                flights.append(act)
            elif "transfer" in title or "pickup" in title or "drop" in title:
                transfers.append(act)

    grand_total = sum(item['total_cost'] for item in accommodation)

    return render(request, 'tour/client_summary.html', {
        'destinations': destinations,
        'accommodation': accommodation,
        'flights': flights,
        'transfers': transfers,
        'grand_total': grand_total,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })


@login_required
def export_summary_excel(request):
    user = request.user
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    destinations = Destination.objects.filter(user=user).prefetch_related('rooms', 'date_ranges')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Accommodation Summary"
    headers = ['Start Date', 'End Date', 'Destination', 'Room', 'Basis', 'Nights', 'Cost', 'Total Cost']
    ws.append(headers)

    for dest in destinations:
        date_ranges = dest.date_ranges.all()
        if start_date:
            date_ranges = date_ranges.filter(end_date__gte=start_date)
        if end_date:
            date_ranges = date_ranges.filter(start_date__lte=end_date)
        for dr in date_ranges:
            for room in dest.rooms.all():
                total = float(room.cost) * int(room.nights)
                ws.append([
                    dr.start_date,
                    dr.end_date,
                    dest.name,
                    room.name,
                    room.basis,
                    room.nights,
                    float(room.cost),
                    total
                ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=accommodation_summary.xlsx'
    wb.save(response)
    return response


@login_required
def export_summary_pdf(request):
    user = request.user
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    destinations = Destination.objects.filter(user=user).prefetch_related('rooms', 'date_ranges', 'images', 'activities')

    accommodation = get_accommodation_summary(destinations, start_date=start_date, end_date=end_date)

    # When rendering images in PDF, prefer absolute URLs:
    for dest in destinations:
        for img in dest.images.all():
            # attach absolute url attribute for template convenience
            try:
                img.abs_url = request.build_absolute_uri(img.image.url)
            except Exception:
                img.abs_url = ""

    ctx = {
        'accommodation': accommodation,
        'destinations': destinations,
        'grand_total': sum(item['total_cost'] for item in accommodation),
        'start_date': start_date_str,
        'end_date': end_date_str,
        'request': request,
    }

    template = get_template('tour/summary_pdf_template.html')
    html = template.render(ctx)

    # Generate PDF to HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="accommodation_summary.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from .models import Destination, DateRange, Room, Activity, TravelLeg
from .forms import TravelLegForm
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum

# list travel legs for user
# list travel legs for user
@login_required
def travel_leg_list(request):
    user = request.user
    legs = TravelLeg.objects.filter(user=user).order_by('date', 'created_at')
    return render(request, 'tour/travel_leg_list.html', {'legs': legs})

# create travel leg (GET/POST)
@login_required
def travel_leg_create(request):
    user = request.user

    # prefill pick_up from last leg's drop_off if exists
    last_leg = TravelLeg.objects.filter(user=user).order_by('-date', '-created_at').first()

    if request.method == 'POST':
        form = TravelLegForm(request.POST)
        if form.is_valid():
            leg = form.save(commit=False)
            leg.user = user
            if form.cleaned_data.get('from_destination') and not leg.pick_up:
                leg.pick_up = form.cleaned_data['from_destination'].name
            if form.cleaned_data.get('to_destination') and not leg.drop_off:
                leg.drop_off = form.cleaned_data['to_destination'].name
            if not leg.pick_up and last_leg:
                leg.pick_up = last_leg.drop_off
            leg.save()
            # 🔹 Redirect without namespace
            return redirect('travel_leg_list')
    else:
        initial = {}
        if last_leg:
            initial['pick_up'] = last_leg.drop_off
        form = TravelLegForm(initial=initial)

    return render(request, 'tour/travel_leg_form.html', {'form': form, 'last_leg': last_leg})


# AJAX to get destination names/dates (if needed)
@login_required
def destination_dates_api(request, destination_id):
    drs = DateRange.objects.filter(destination_id=destination_id)
    dates = []
    for dr in drs:
        current = dr.start_date
        while current <= dr.end_date:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
    return JsonResponse({'dates': dates})

# Updated client summary view
@login_required
def client_summary_view(request):
    user = request.user
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    destinations = Destination.objects.filter(user=user).prefetch_related(
        'rooms', 'date_ranges', 'images', 'activities', 'restaurants', 'info'
    )

    # accommodation summary (reuse your get_accommodation_summary if present)
    accommodation = get_accommodation_summary(destinations, start_date=start_date, end_date=end_date)

    # flights and transfers from TravelLeg
    flights_qs = TravelLeg.objects.filter(user=user, booking_type='flight').order_by('date', 'created_at')
    transfers_qs = TravelLeg.objects.filter(user=user, booking_type='transfer').order_by('date', 'created_at')

    # optionally filter by date range
    if start_date:
        flights_qs = flights_qs.filter(date__gte=start_date)
        transfers_qs = transfers_qs.filter(date__gte=start_date)
    if end_date:
        flights_qs = flights_qs.filter(date__lte=end_date)
        transfers_qs = transfers_qs.filter(date__lte=end_date)

    flights = list(flights_qs)
    transfers = list(transfers_qs)

    # sums
    acc_total = sum(Decimal(item['total_cost']) for item in accommodation) if accommodation else Decimal('0.00')
    flights_total = flights_qs.aggregate(total=Sum('cost'))['total'] or Decimal('0.00')
    transfers_total = transfers_qs.aggregate(total=Sum('cost'))['total'] or Decimal('0.00')

    grand_total = acc_total + Decimal(flights_total) + Decimal(transfers_total)

    return render(request, 'tour/client_summary.html', {
        'destinations': destinations,
        'accommodation': accommodation,
        'flights': flights,
        'transfers': transfers,
        'grand_total': grand_total,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })

@login_required
def travel_summary(request):
    user = request.user

    accommodation = Accommodation.objects.filter(user=user)
    flights = TravelLeg.objects.filter(user=user, booking_type='flight').order_by('date')
    transfers = TravelLeg.objects.filter(user=user, booking_type='transfer').order_by('date')

    grand_total = (
        sum(acc.total_cost for acc in accommodation) +
        sum(f.cost for f in flights) +
        sum(t.cost for t in transfers)
    )

    context = {
        'accommodation': accommodation,
        'flights': flights,
        'transfers': transfers,
        'grand_total': grand_total,
    }
    return render(request, 'travel_summary.html', context)



def home(request,):
    return render(request, 'tour/home.html',)

@login_required(login_url='login')
def dashboard(request):
    q=request.GET.get('q') if request.GET.get('q') != None else ''
    bookings=Booking.objects.filter(
        Q(email__icontains=q) | 
        Q(phone__icontains=q)|
        Q(origin_location__icontains=q)
    )
    itinerary= Itinerary.objects.all()
    context={'bookings':bookings, 'itinerary':itinerary}
    return render(request,'tour/dashboard.html',context)

@login_required(login_url='login')
def clientList(request):
    bookings=Booking.objects.all()
    context={'bookings':bookings}
    return render(request,'tour/client_list.html',context)


@login_required(login_url='login')
def clientDetails(request,pk):
    bookings=Booking.objects.get(id=pk)
    context={"bookings":bookings}
    return render(request,'tour/client_details.html', context)

@login_required(login_url='login')
def itinerary(request):
    itinerary= Itinerary.objects.all()
    context={'itinerary':itinerary}
    return render(request, 'tour/itinerary.html',context)



@login_required(login_url='login')
def newBooking(request):
    form=BookingForm()
    if request.method=="POST":
        form=BookingForm(request.POST)
        if form.is_valid():
            form.save()
           # return HttpResponse("Booking created successfully")
            return redirect('dashboard')
    context={'form':form}

    return render(request, 'tour/newBookingForm.html', context)

@login_required(login_url='login')
def newItinerary(request):
    form=ItineraryForm()
    if request.method=='POST':
        form=ItineraryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    context={'form':form}
    return render(request, 'tour/newItineraryForm.html', context)



@login_required(login_url='login')
def updateBooking(request,pk):
    booking=Booking.objects.get(id=pk)
    form=BookingForm(instance=booking)
    if request.method=='POST':
        form=BookingForm(request.POST,instance=booking)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    context={'form':form}
    return render(request,'tour/newBookingForm.html', context)


@login_required(login_url='login')
def updateItinerary(request,pk):
    itinerary=Itinerary.objects.get(id=pk)
    form=ItineraryForm(instance=itinerary)
    if request.method=='POST':
        form=ItineraryForm(request.POST,instance=itinerary)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    context={'form':form}
    return render(request,'tour/newItineraryForm.html', context)


@login_required(login_url='login')
def deleteBooking(request,pk):
    booking=Booking.objects.get(id=pk)
    if request.method=='POST':
        booking.delete()
        return redirect('dashboard')

    context={'obj':booking}
    return render(request, 'tour/delete.html',context)


@login_required(login_url='login')
def deleteItinerary(request,pk):
    itinerary=Itinerary.objects.get(id=pk)
    if request.method=='POST':
        itinerary.delete()
        return redirect('dashboard')

    context={'obj':itinerary}
    return render(request, 'tour/delete.html',context)


@login_required(login_url='login')
def userProfile(request,pk):
    user=User.objects.get(id=pk)
    context={'user':user}
    return render(request, 'tour/profile.html',context)








# Create your views here.
