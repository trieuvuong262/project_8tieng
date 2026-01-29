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
def my_profile(request):
    user = request.user

    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user, total_kpi_points=100, level_rank="Thực tập sinh"
        )
        if user.is_superuser:
            profile.total_kpi_points = 99999
            profile.job_title = "Quản Trị Viên Hệ Thống"
            profile.save()

    if request.method == "POST":

        avatar_seed = request.POST.get("avatar_seed")
        if avatar_seed:
            try:

                img_url = (
                    f"https://api.dicebear.com/7.x/avataaars/svg?seed={avatar_seed}"
                )

                with urllib.request.urlopen(img_url) as response:
                    img_content = response.read()

                    profile.avatar.save(
                        f"{avatar_seed}.svg", ContentFile(img_content), save=True
                    )
                    messages.success(request, "Đã cập nhật Avatar mới!")
            except Exception as e:
                messages.error(request, f"Lỗi khi lưu avatar: {e}")

        if "avatar_upload" in request.FILES:
            profile.avatar = request.FILES["avatar_upload"]
            profile.save()
            messages.success(request, "Đã tải ảnh lên thành công!")

        return redirect("my_profile")

    points = profile.total_kpi_points
    rank = "Thực tập sinh"
    if points >= 1000:
        rank = "Nhân viên chính thức"
    if points >= 5000:
        rank = "Trưởng nhóm"
    if points >= 10000:
        rank = "Giám đốc"
    if user.is_superuser:
        rank = "Administrator (VIP)"

    if profile.level_rank != rank:
        profile.level_rank = rank
        profile.save()

    notifications = user.notifications.all().order_by("-created_at")

    all_posts = Confession.objects.filter(author=user).order_by("-created_at")

    avatar_options = [
        "Felix",
        "Aneka",
        "Zoe",
        "Jack",
        "Bella",
        "Bandit",
        "Mimi",
        "Tigger",
        "Spooky",
        "Bubba",
        "Cuddles",
        "Whiskers",
        "Peanut",
        "Shadow",
        "Midnight",
    ]

    context = {
        "profile": profile,
        "notifications": notifications,
        "my_posts": all_posts,
        "rank": rank,
        "avatar_options": avatar_options,
    }

    return render(request, "core/profile.html", context)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:

        UserProfile.objects.create(
            user=instance, total_kpi_points=100, level_rank="Thực tập sinh"
        )


def register(request):
    """Trang đăng ký thành viên mới"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            messages.success(
                request,
                f"Chào mừng {user.username}! Bạn được tặng 100 điểm KPI làm vốn.",
            )
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "core/register.html", {"form": form})