from divassist_web.forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth import views as auth_views
from divassist_web.models import *
import re

# Rides
from django.utils import timezone

import os
import requests, json

 
@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            login(request, user)
            return HttpResponseRedirect('/registration/select_home_station/')
    elif request.user.is_authenticated():
        return HttpResponseRedirect('/home_page/')
    else:
        form = RegistrationForm()
 
    return render(request, 'divassist_web/registration/register.html', {
		'form': form
	})


def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')


def select_home_station(request):
    if request.method == 'POST':
        form = HomeStationSelectionForm(request.POST)
        if form.is_valid():
            form.submit()
            return HttpResponseRedirect('/home_page/')
    else:
        form = HomeStationSelectionForm()
    return render(request, 
        'divassist_web/registration/select_home_station.html',{
        'user': request.user,
        'form': form
    })


def login_page(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/home_page/')
    else:
        return auth_views.login(request, template_name='divassist_web/registration/login.html')


@login_required
def home_page(request):
    return render(request, 'divassist_web/home_page.html', {
        'user': request.user
    })

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return HttpResponseRedirect('/home_page/')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'divassist_web/registration/change_password.html', {
        'user': request.user,
        'form': form
    })

# Rides
def add_ride(request):
    if request.method == 'POST':
        form = RideForm(request.POST)
        if form.is_valid():
            # Create new ride
            new_ride = Ride(
                title_text=form.cleaned_data['title_text'],
                pub_date=timezone.now(),
                desc_text=form.cleaned_data['desc_text'],
                s_neighborhood=form.cleaned_data['s_neighborhood'],
                e_neighborhood=form.cleaned_data['e_neighborhood'],
                difficulty=form.cleaned_data['difficulty'],
                # owner=UserProfile.objects.get(user=request.user)
                owner=request.user
            )
            new_ride.save()
            
            # Create stops along the way
            stop = form.cleaned_data['stop']
            new_stop = Stop(ride=new_ride, number=stop, station=burr)
            new_stop.save()
            
            # Associate tags with ride, creating tag if it doesn't already exist
            tags_string = form.cleaned_data['tags']
            tags_array = list(filter(None, re.split(',| ', tags_string)))   # tokenize by comma and space
            for tag_name in tags_array:
                found_tag = Tag.objects.filter(tag=tag_name).first()
                if not found_tag:
                    new_tag = Tag(tag=tag_name)
                    new_tag.save()
                    found_tag = new_tag
                found_tag.rides.add(new_ride)
            
            # Return ride_created page
            return HttpResponseRedirect('/rides/ride_created/')
    # GET, etc.
    else:
        form = RideForm()
    # return render(request, 'divassist_web/rides/add_ride.html', {
    return render(request, 'divassist_web/upload_ride.html', {
		'form': form
	})

def ride_created(request):
    ride = Ride.objects.last()
    return render(request, 'divassist_web/rides/ride_created.html', {
        'user': request.user,
        'ride': ride,
        'tags': Tag.objects.filter(rides=ride)
    })

def search_ride(request):
    if request.method == 'POST':
        form = SearchRideForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            desc_keywords = form.cleaned_data['desc_keywords']
            start_neighborhood = form.cleaned_data['start_neighborhood']
            end_neighborhood = form.cleaned_data['end_neighborhood']
            diffType = form.cleaned_data['difftype']
            difficulty = form.cleaned_data['difficulty']
            tags_string = form.cleaned_data['tags']
            
            qset = Ride.objects.all()
            if (title):
                qset = qset.filter(title_text__icontains=title)
            if (desc_keywords):
                qset = qset.filter(desc_text__icontains=desc_keywords)
            if (start_neighborhood):
                qset = qset.filter(s_neighborhood__icontains=start_neighborhood)
            if (end_neighborhood):
                qset = qset.filter(e_neighborhood__icontains=end_neighborhood)
            if (difficulty and diffType):
                if(diffType == '1'):
                    qset = qset.filter(difficulty__lte=difficulty)
                if(diffType == '2'):
                    qset = qset.filter(difficulty__gt=difficulty)
                if(diffType == '3'):
                    qset = qset.filter(difficulty=difficulty)
            if (tags_string):
                tags_array = list(filter(None, re.split(',| ', tags_string)))   # tokenize by comma and space
                for tag_name in tags_array:
                    qset = qset.filter(tag__tag=tag_name)
            filtered_rides = qset.order_by('-pub_date', 'difficulty')
            # return HttpResponseRedirect('/view_rides/') # Not made yet
            # return render(request, 'divassist_web/rides/view_rides.html', {
                # 'rides': rides
            # })
            return view_specific_rides(request, filtered_rides)
    else:
        form = SearchRideForm()
    # return render(request, 'divassist_web/rides/search_rides.html', {
    return render(request, 'divassist_web/search_ride.html', {
        'form': form
    })

def view_all_rides(request):
    all_rides = Ride.objects.all()
    # A list of lists of tags to pass into template
    # I really can't think of a better way with our current design
    tags = []
    for ride in all_rides:
        ride_tags = Tag.objects.filter(rides=ride)
        tags.append(ride_tags)
    rides_and_tags = zip(all_rides, tags)
    # return render(request, 'divassist_web/rides/view_ride.html', {
    return render(request, 'divassist_web/view_ride.html', {
        'user': request.user,
        'rides_and_tags': rides_and_tags    # zipped list of rides and tags
    })

def view_specific_rides(request, rides):
    # A list of lists of tags to pass into template
    # I really can't think of a better way with our current design
    tags = []
    for ride in rides:
        ride_tags = Tag.objects.filter(rides=ride)
        tags.append(ride_tags)
    rides_and_tags = zip(rides, tags)
    # return render(request, 'divassist_web/rides/view_ride.html', {
    return render(request, 'divassist_web/view_ride.html', {
        'user': request.user,
        'rides_and_tags': rides_and_tags
    })

def landing(request, time):
    # 0 - morning, 1 - afternoon, 2 - evening
    return render(request, 'divassist_web/landing.html', {
        'time': time
    })

@login_required
def prediction(request, day, hour):
    # convert numerical day to 3-letter day
    num_to_day = {
        "0": "Sun",
        "1": "Mon",
        "2": "Tue",
        "3": "Wed",
        "4": "Thu",
        "5": "Fri",
        "6": "Sat"
    }
    day_of_week = num_to_day[day]

    # get the predictions for specified day/time
    predictions = Prediction.objects.filter(day_of_week=day_of_week, start_hour=int(hour))

    return render(request, 'divassist_web/prediction.html', {
        'google_maps_key': os.environ['GOOGLE_MAPS_KEY'],
        'predictions': predictions
    })