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

def get_random_pseudonym():
    """Tạo tên ẩn danh ngẫu nhiên cho Confession"""
    adjectives = ["Mèo", "Cá Mập", "Gấu", "Thỏ", "Sóc", "Cú", "Hổ"]
    nouns = ["Kế Toán", "IT", "Sale", "Marketing", "HR", "Intern", "Designer"]
    colors = ["Béo", "Cận", "Thông Thái", "Vui Vẻ", "Trầm Cảm", "Ngây Thơ"]

    return f"{random.choice(adjectives)} {random.choice(nouns)} {random.choice(colors)}"
def confession_feed(request):
    """
    Hiển thị danh sách bài viết, xử lý đăng bài mới & bộ lọc
    """

    if request.method == "POST" and "submit_confession" in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để đăng bài.")
            return redirect("login")

        content = request.POST.get("content")
        custom_pseudo = request.POST.get("pseudonym")
        company_input = request.POST.get("company_name")

        is_anon_status = request.POST.get("is_anonymous") == "on"

        if content:

            if custom_pseudo and custom_pseudo.strip():
                final_name = custom_pseudo.strip()

            else:
                final_name = request.user.username

            Confession.objects.create(
                content=content,
                author=request.user,
                pseudonym=final_name,
                company_name=company_input,
                is_anonymous=is_anon_status,
                status="PENDING",
            )
            messages.success(request, "Đã gửi bài viết! Vui lòng chờ Admin duyệt.")
        return redirect("confession_feed")

    base_query = Confession.objects.filter(status="APPROVED")

    if request.user.is_authenticated:
        base_query = base_query.exclude(hiddenpost__user=request.user)

        user_reaction_subquery = Reaction.objects.filter(
            post=OuterRef("pk"), user=request.user
        ).values("reaction_type")[:1]

        base_query = base_query.annotate(
            current_user_reaction=Subquery(user_reaction_subquery)
        )

    comments_prefetch = Prefetch(
        "comments",
        queryset=Comment.objects.select_related("author").order_by("created_at"),
    )
    base_query = base_query.select_related("author").prefetch_related(comments_prefetch)

    filter_type = request.GET.get("filter", "newest")

    if filter_type == "top":
        confession_list = base_query.order_by("-loves_count")
    elif filter_type == "drama":
        confession_list = base_query.order_by("-comments_count")
    else:
        confession_list = base_query.order_by("-created_at")

    paginator = Paginator(confession_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/confession_feed.html",
        {"confessions": page_obj, "active_filter": filter_type},
    )

def submit_comment(request, post_id):
    """
    Xử lý gửi bình luận (Hỗ trợ Ẩn danh & Trả lời)
    """
    if request.method == "POST":
        post = get_object_or_404(Confession, id=post_id)
        content = request.POST.get("comment_content")
        parent_id = request.POST.get("parent_id")

        is_anonymous_comment = request.POST.get("is_anonymous") == "on"

        if content:
            parent_comment = None
            if parent_id:
                parent_comment = Comment.objects.filter(id=parent_id).first()

            Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent_comment,
                is_anonymous=is_anonymous_comment,
            )

            post.comments_count = F("comments_count") + 1
            post.save()

    return redirect(f"/social/?filter=newest#post-{post_id}")


@login_required
def api_report_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Confession, id=post_id)
        reason = request.POST.get("reason", "Spam hoặc nội dung xấu")

        PostReport.objects.create(user=request.user, post=post, reason=reason)
        messages.success(request, "Đã gửi báo cáo cho Admin xem xét.")
        return redirect("confession_feed")


@login_required
def api_hide_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Confession, id=post_id)

        HiddenPost.objects.get_or_create(user=request.user, post=post)
        messages.success(request, "Đã ẩn bài viết này vĩnh viễn.")
        return redirect("confession_feed")


@login_required
def api_like_confession(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Confession, id=post_id)
        post.likes_count = F("likes_count") + 1
        post.save()

        post.refresh_from_db()
        return JsonResponse({"success": True, "new_likes": post.likes_count})
    return JsonResponse({"success": False}, status=400)


@login_required
def api_react_confession(request, post_id, reaction_type):
    """
    reaction_type: 'LOVE' hoặc 'ANGRY'
    """
    if request.method == "POST":
        post = get_object_or_404(Confession, id=post_id)
        user = request.user

        existing_reaction = Reaction.objects.filter(user=user, post=post).first()

        action = "added"

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:

                existing_reaction.delete()
                if reaction_type == "LOVE":
                    post.loves_count = F("loves_count") - 1
                else:
                    post.angry_count = F("angry_count") - 1
                action = "removed"
            else:

                if existing_reaction.reaction_type == "LOVE":
                    post.loves_count = F("loves_count") - 1
                else:
                    post.angry_count = F("angry_count") - 1

                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()

                if reaction_type == "LOVE":
                    post.loves_count = F("loves_count") + 1
                else:
                    post.angry_count = F("angry_count") + 1
                action = "switched"
        else:

            Reaction.objects.create(user=user, post=post, reaction_type=reaction_type)
            if reaction_type == "LOVE":
                post.loves_count = F("loves_count") + 1
            else:
                post.angry_count = F("angry_count") + 1

        post.save()
        post.refresh_from_db()

        return JsonResponse(
            {
                "success": True,
                "action": action,
                "loves": post.loves_count,
                "angries": post.angry_count,
            }
        )

    return JsonResponse({"success": False}, status=400)
