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

@login_required
def shop_page(request):

    products = Product.objects.filter(is_active=True).order_by("-created_at")

    if request.method == "POST" and "redeem_product" in request.POST:
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        user_profile = request.user.profile

        if user_profile.total_kpi_points >= product.price:

            user_profile.total_kpi_points -= product.price
            user_profile.save()

            messages.success(
                request,
                f"Chúc mừng! Bạn đã đổi thành công {product.name}. Admin sẽ liên hệ giao quà nhé!",
            )
            return redirect("shop_page")
        else:
            messages.error(
                request, "Rất tiếc! Bạn chưa đủ điểm KPI để đổi món quà này."
            )

    context = {
        "products": products,
        "categories": ["Cây xanh", "Đèn bàn", "Phụ kiện", "Tượng/Mô hình"],
    }
    return render(request, "core/shop_page.html", context)
