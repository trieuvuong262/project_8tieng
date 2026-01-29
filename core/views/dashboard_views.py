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

def get_time_context():
    """
    Xác định ngữ cảnh dựa trên giờ hiện tại.
    Trả về: (mode_string, greeting_title, greeting_sub)
    """
    hour = datetime.now().hour

    if 5 <= hour < 9:
        return (
            "morning",
            "Chào buổi sáng!",
            "Hôm nay Deadline thế nào, đã sẵn sàng chiến đấu chưa?",
        )
    elif 9 <= hour < 11 or 13 <= hour < 16:
        return (
            "work",
            "Giờ làm việc tập trung",
            "Tắt Facebook đi, làm xong sớm về sớm nào!",
        )
    elif 11 <= hour < 13:
        return "lunch", "Nghỉ trưa thôi!", "11h30 rồi, chuẩn bị order cơm chưa?"
    elif 16 <= hour < 18:
        return "chill", "Sắp được về rồi!", "Cố lên, chỉ còn một chút nữa thôi."
    else:
        return (
            "chill",
            "Tan làm rồi!",
            "Về nhà nghỉ ngơi hoặc lượn lờ shop decor chút không?",
        )

def dashboard(request):
    time_mode, greeting_title, greeting_sub = get_time_context()
    quotes = DailyQuote.objects.filter(time_category=time_mode, is_active=True)
    if quotes.exists():
        daily_quote = random.choice(list(quotes))
    else:

        daily_quote = {
            "content": "Chúc bạn một ngày làm việc hiệu quả và tràn đầy năng lượng!",
            "author": "Hệ thống",
        }

    widget_template = "core/widgets/guest_widget.html"
    if request.user.is_authenticated:
        today = timezone.now().date()
        has_checked_in = CheckIn.objects.filter(user=request.user, date=today).exists()
        widget_template = (
            "core/widgets/stats_widget.html"
            if has_checked_in
            else "core/widgets/checkin_widget.html"
        )

    try:
        restaurants = Restaurant.objects.all().order_by("-rating")[:8]
    except:
        restaurants = []

    try:
        dishes_db = list(Dish.objects.values_list("name", flat=True))
    except:
        dishes_db = []

    if dishes_db:
        food_list = dishes_db
    else:
        food_list = [
            "Cơm tấm sườn bì",
            "Bún đậu mắm tôm",
            "Phở bò tái nạm",
            "Cơm gà xối mỡ",
            "Healthy Salad",
            "Bánh mì chảo",
            "Mì ý sốt kem",
        ]

    today_food = random.choice(food_list)

    dishes_json = json.dumps(food_list)

    office_tools = [
        {"name": "Chuyển File", "desc": "PDF, Word, Excel...", "icon": "file-type-2"},
        {"name": "OCR Ảnh", "desc": "Lấy text từ hình ảnh", "icon": "scan-text"},
        {"name": "Nén Ảnh", "desc": "Giảm dung lượng nhanh", "icon": "image-minus"},
        {"name": "AI Assistant", "desc": "Chat với AI", "icon": "bot"},
        {"name": "Xóa Background", "desc": "Tách nền ảnh", "icon": "eraser"},
        {"name": "Tạo mã QR", "desc": "Tạo QR link, Wifi...", "icon": "qr-code"},
        {"name": "Ghi chú", "desc": "Note nhanh ý tưởng", "icon": "sticky-note"},
        {"name": "File Mẫu", "desc": "Hợp đồng, đơn từ...", "icon": "files"},
        {"name": "Download", "desc": "Bộ cài phần mềm", "icon": "download-cloud"},
        {"name": "Lương Net", "desc": "Tính Gross sang Net", "icon": "calculator"},
        {"name": "BHTN", "desc": "Bảo hiểm thất nghiệp", "icon": "landmark"},
        {"name": "Giờ Về", "desc": "Đếm ngược tan làm", "icon": "timer"},
    ]

    decor_items = Product.objects.filter(is_active=True, is_hot=True).order_by("-id")[
        :4
    ]

    if decor_items.count() < 4:
        decor_items = Product.objects.filter(is_active=True).order_by("-id")[:4]

    health_tips = [
        {
            "title": "Quy tắc 20-20-20",
            "content": "Cứ 20 phút nhìn màn hình, hãy nhìn xa 20 feet (6m) trong 20 giây để bảo vệ mắt.",
        },
        {
            "title": "Uống nước đúng cách",
            "content": "Đừng đợi khát mới uống. Hãy đặt một cốc nước ngay tại bàn làm việc.",
        },
        {
            "title": "Tư thế ngồi chuẩn",
            "content": "Giữ lưng thẳng, màn hình ngang tầm mắt để tránh đau cổ vai gáy.",
        },
    ]
    health_tip = random.choice(health_tips)

    latest_confessions = (
        Confession.objects.filter(status="APPROVED")
        .select_related("author")
        .order_by("-created_at")[:2]
    )
    top_users = UserProfile.objects.select_related("user").order_by(
        "-total_kpi_points"
    )[:3]

    context = {
        "time_mode": time_mode,
        "greeting_title": greeting_title,
        "greeting_sub": greeting_sub,
        "daily_quote": daily_quote,
        "widget_template": widget_template,
        "today_food": today_food,
        "dishes_json": dishes_json,
        "restaurants": restaurants,
        "office_tools": office_tools[:4],
        "latest_confessions": latest_confessions,
        "top_users": top_users,
        "decor_items": decor_items,
        "health_tip": health_tip,
    }

    return render(request, "core/dashboard.html", context)
@login_required
def daily_checkin(request):
    if request.method == "POST":
        today = timezone.now().date()

        checkin, created = CheckIn.objects.get_or_create(user=request.user, date=today)

        if created:

            profile = request.user.profile
            profile.total_kpi_points += 10
            profile.save()
            messages.success(request, "Điểm danh thành công! +10 KPI Points 🚀")
        else:
            messages.info(request, "Bạn đã điểm danh hôm nay rồi.")

    return redirect("home")