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

@staff_member_required(login_url="login")
def moderation_dashboard(request):
    """
    Dashboard quản trị viên trung tâm (All-in-one).
    Xử lý: Confession, Health Config, Pantry, Quote.
    """

    current_tab = request.GET.get("tab", "confession")
    current_filter = request.GET.get("filter", "pending")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            post = get_object_or_404(Confession, id=request.POST.get("post_id"))
            post.status = "APPROVED"
            post.save()
            messages.success(request, f"✅ Đã duyệt bài #{post.id}")

        elif action == "reject":
            post = get_object_or_404(Confession, id=request.POST.get("post_id"))
            post.status = "REJECTED"
            post.save()
            messages.warning(request, f"🚫 Đã từ chối bài #{post.id}")

        elif action == "send_notification":
            target_type = request.POST.get("target_type")
            target_username = request.POST.get("target_username")
            title = request.POST.get("noti_title")
            content = request.POST.get("noti_content")
            noti_type = request.POST.get("noti_type", "SYSTEM")

            if target_type == "ALL":
                users = User.objects.all()
                Notification.objects.bulk_create(
                    [
                        Notification(
                            user=u,
                            title=title,
                            content=content,
                            notification_type=noti_type,
                        )
                        for u in users
                    ]
                )
                messages.success(request, f"📢 Đã gửi đến {users.count()} user.")
            elif target_type == "SINGLE":
                try:
                    user = User.objects.get(username=target_username)
                    Notification.objects.create(
                        user=user,
                        title=title,
                        content=content,
                        notification_type=noti_type,
                    )
                    messages.success(request, f"📨 Đã gửi đến {target_username}.")
                except User.DoesNotExist:
                    messages.error(request, "Không tìm thấy user.")

        elif action == "add_quote":
            content = request.POST.get("content")
            author = request.POST.get("author", "Sếp ẩn danh")
            time_cat = request.POST.get("time_category")
            if content and time_cat:
                DailyQuote.objects.create(
                    content=content,
                    author=author,
                    time_category=time_cat,
                    is_active=True,
                )
                messages.success(request, "✨ Đã thêm câu quote mới!")
            else:
                messages.error(request, "Vui lòng nhập đầy đủ nội dung.")
            return redirect(f"{request.path}?tab=quote")

        elif action == "delete_quote":
            quote_id = request.POST.get("quote_id")
            DailyQuote.objects.filter(id=quote_id).delete()
            messages.success(request, "🗑️ Đã xóa câu quote thành công.")
            return redirect(f"{request.path}?tab=quote")

        elif action == "toggle_quote":
            quote_id = request.POST.get("quote_id")
            quote = get_object_or_404(DailyQuote, id=quote_id)
            quote.is_active = not quote.is_active
            quote.save()

            messages.success(request, "🔄 Đã cập nhật trạng thái quote.")
            return redirect(f"{request.path}?tab=quote")
        
        elif action == "add_product":
            try:
                # Lấy dữ liệu từ form HTML
                p_name = request.POST.get("p_name")
                p_price_text = request.POST.get("p_price_text") # Giá dạng chữ (VD: 200k)
                p_link = request.POST.get("p_link")             # Link Affiliate
                p_category = request.POST.get("p_category")
                p_image = request.FILES.get("p_image")

                # Kiểm tra dữ liệu bắt buộc
                if p_name and p_link and p_image:
                    Product.objects.create(
                        name=p_name,
                        price_display=p_price_text, # Lưu giá text
                        affiliate_url=p_link,       # Lưu link
                        category=p_category,
                        image=p_image,
                        is_active=True
                    )
                    messages.success(request, f"Đã đăng sản phẩm '{p_name}' thành công!")
                else:
                    messages.error(request, "Thiếu tên, link sản phẩm hoặc ảnh!")
            
            except Exception as e:
                messages.error(request, f"Lỗi hệ thống: {str(e)}")
            
            return redirect(f"{request.path}?tab=shop")

        elif action == "update_health_config":
            codes = ["yoga", "wrist", "meditation", "music", "back"]
            for code in codes:
                new_id = request.POST.get(f"video_{code}")
                if new_id is not None:
                    HealthExercise.objects.update_or_create(
                        code=code,
                        defaults={
                            "title": code.capitalize(),
                            "youtube_id": new_id.strip(),
                        },
                    )
            messages.success(request, "✅ Đã cập nhật cấu hình Relax!")
            return redirect(f"{request.path}?tab=relax")

        elif action == "add_restaurant":
            try:
                name = request.POST.get("res_name")
                address = request.POST.get("res_address")
                new_res = Restaurant.objects.create(
                    name=name,
                    address=address,
                    url_foody=request.POST.get("res_url"),
                    image=request.FILES.get("res_image"),
                    category=request.POST.get("res_category", "Món ngon"),
                    rating=5.0,
                )
                messages.success(request, f"Đã thêm quán '{name}' thành công!")
            except Exception as e:
                messages.error(request, f"Lỗi: {str(e)}")
            return redirect(f"{request.path}?tab=pantry")

        if current_tab == "confession":
            return redirect(f"{request.path}?tab=confession&filter={current_filter}")

    posts = []
    reports = []
    health_configs = {}
    pantry_restaurants = []
    all_quotes = []
    products = []

    if current_tab == "confession":
        if current_filter == "approved":
            post_list = (
                Confession.objects.filter(status="APPROVED")
                .prefetch_related("comments__author")
                .order_by("-created_at")
            )
            paginator = Paginator(post_list, 20)
            posts = paginator.get_page(request.GET.get("page"))
        elif current_filter == "reports":
            reports = (
                PostReport.objects.filter(is_resolved=False)
                .select_related("post", "user")
                .order_by("-created_at")
            )
        else:
            post_list = Confession.objects.filter(status="PENDING").order_by(
                "created_at"
            )
            paginator = Paginator(post_list, 50)
            posts = paginator.get_page(request.GET.get("page"))

    elif current_tab == "relax":
        exercises = HealthExercise.objects.all()
        health_configs = {ex.code: ex.youtube_id for ex in exercises}

    elif current_tab == "pantry":
        pantry_restaurants = Restaurant.objects.all().order_by("-id")

    elif current_tab == "quote":
        all_quotes = DailyQuote.objects.all().order_by("-id")
        
    elif current_tab == "shop":
        products = Product.objects.all().order_by("-created_at")

    stats = {
        "pending": Confession.objects.filter(status="PENDING").count(),
        "approved": Confession.objects.filter(status="APPROVED").count(),
        "reports": PostReport.objects.filter(is_resolved=False).count(),
    }

    context = {
        "current_tab": current_tab,
        "current_filter": current_filter,
        "posts": posts,
        "reports": reports,
        "health_configs": health_configs,
        "pantry_restaurants": pantry_restaurants,
        "all_quotes": all_quotes,
        "stats": stats,
        "products": products,
    }

    return render(request, "core/moderation.html", context)