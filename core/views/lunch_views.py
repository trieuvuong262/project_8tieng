import random
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count
from django.db.models import F, OuterRef, Subquery, Prefetch
from core.models import (
    DailyQuote,
    Dish,
    HealthExercise,
    Restaurant,
    UserProfile,
    PointHistory,
    Confession,
    Comment,
    Reaction,
    CheckIn,
    DocumentResource,
    Product,
    FoodReview,
    Notification,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import PostReport, HiddenPost

OuterRef, Subquery

from django.core.paginator import Paginator
import requests
from django.core.files.base import ContentFile
import urllib.request

def lunch_page(request):

    API_KEY = "00600188ac064b66a7940d1ce0d3800a"

    lat_param = request.GET.get("lat")
    lon_param = request.GET.get("lon")
    radius_param = request.GET.get("radius", "1000")

    page_db_num = request.GET.get("page_db", 1)
    page_api_num = request.GET.get("page_api", 1)

    try:
        radius = int(radius_param)
        if radius < 500:
            radius = 500
        if radius > 10000:
            radius = 10000
    except:
        radius = 1000

    if lat_param and lon_param:
        LAT = lat_param
        LON = lon_param
    else:
        LAT = "10.7716"
        LON = "106.7044"

    base_params = f"lat={LAT}&lon={LON}&radius={radius}"

    try:

        db_all_list = Restaurant.objects.all().order_by("-rating")
    except:
        db_all_list = []

    paginator_db = Paginator(db_all_list, 8)

    db_restaurants = paginator_db.get_page(page_db_num)

    url = f"https://api.geoapify.com/v2/places?categories=catering.restaurant&filter=circle:{LON},{LAT},{radius}&bias=proximity:{LON},{LAT}&limit=24&apiKey={API_KEY}"

    api_list_raw = []

    food_images = [
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=500&q=80",
    ]

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            for feature in features:
                props = feature.get("properties", {})
                if not props.get("name"):
                    continue

                res = {
                    "name": props.get("name"),
                    "address": props.get(
                        "address_line2", props.get("address_line1", "Đang cập nhật")
                    ),
                    "rating": round(random.uniform(4.0, 5.0), 1),
                    "review_count": random.randint(20, 150),
                    "category": props.get("datasource", {})
                    .get("raw", {})
                    .get("cuisine", "Món ngon"),
                    "image": {"url": random.choice(food_images)},
                    "url_foody": f"http://googleusercontent.com/maps.google.com/?q={props.get('lat')},{props.get('lon')}",
                    "is_google": True,
                }
                api_list_raw.append(res)
    except Exception as e:
        print(f"Lỗi API: {e}")

    paginator_api = Paginator(api_list_raw, 8)

    api_restaurants = paginator_api.get_page(page_api_num)

    try:
        dishes_db = list(Dish.objects.values_list("name", flat=True))

        api_names = [r["name"] for r in api_list_raw]
        full_list = dishes_db + api_names
    except:
        full_list = []

    food_list = full_list if full_list else ["Cơm tấm", "Phở bò", "Bún chả", "Mì Ý"]
    dishes_json = json.dumps(food_list[:60])

    context = {
        "db_restaurants": db_restaurants,
        "api_restaurants": api_restaurants,
        "dishes_json": dishes_json,
        "current_radius": radius,
        "base_params": base_params,
    }
    return render(request, "core/lunch.html", context)