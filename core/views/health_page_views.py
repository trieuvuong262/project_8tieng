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
def health_page(request):

    exercises_db = HealthExercise.objects.all()

    exercises = {ex.code: ex for ex in exercises_db}

    default_data = {
        "yoga": "s-7lyvblFNI",
        "wrist": "QZjkZa4NxNg",
        "meditation": "O-6f5wQXSu8",
        "music": "jfKfPfyJRdk",
    }

    quotes = [
        "Hít vào tâm tĩnh lặng, thở ra miệng mỉm cười.",
        "Công việc là quả bóng cao su, sức khỏe là quả bóng thủy tinh.",
        "Đừng gồng nữa, cột sống của bạn đang khóc đấy!",
        "Chỉ mất 5 phút để sạc lại năng lượng cho 2 giờ làm việc tiếp theo.",
    ]

    context = {
        "quote": random.choice(quotes),
        "exercises": exercises,
        "defaults": default_data,
    }
    return render(request, "core/health_page.html", context)