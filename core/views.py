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
from .models import (
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
from .models import PostReport, HiddenPost

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


def get_random_pseudonym():
    """Tạo tên ẩn danh ngẫu nhiên cho Confession"""
    adjectives = ["Mèo", "Cá Mập", "Gấu", "Thỏ", "Sóc", "Cú", "Hổ"]
    nouns = ["Kế Toán", "IT", "Sale", "Marketing", "HR", "Intern", "Designer"]
    colors = ["Béo", "Cận", "Thông Thái", "Vui Vẻ", "Trầm Cảm", "Ngây Thơ"]

    return f"{random.choice(adjectives)} {random.choice(nouns)} {random.choice(colors)}"


def dashboard(request):
    time_mode, greeting_title, greeting_sub = get_time_context()
    quotes = DailyQuote.objects.filter(time_category=time_mode, is_active=True)
    if quotes.exists():
        daily_quote = random.choice(list(quotes))
    else:
        # Nếu chưa có quote cho buổi này, lấy câu mặc định
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
        "time_mode": time_mode,  # Thêm cái này
        "greeting_title": greeting_title,  # Thêm cái này
        "greeting_sub": greeting_sub,  # Thêm cái này
        "daily_quote": daily_quote,  # CỰC KỲ QUAN TRỌNG: Thêm cái này
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


def tool_page(request):
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
    return render(request, "core/tool_page.html", {"all_tools": office_tools})


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


@staff_member_required(login_url="login")
def moderation_dashboard(request):
    """
    Dashboard quản trị viên trung tâm (All-in-one).
    Xử lý: Confession, Health Config, Pantry, Quote.
    """
    # Lấy tham số điều hướng
    current_tab = request.GET.get("tab", "confession")
    current_filter = request.GET.get("filter", "pending")

    # --- PHẦN 1: XỬ LÝ POST (HÀNH ĐỘNG CỦA ADMIN) ---
    if request.method == "POST":
        action = request.POST.get("action")

        # 1.1 NHÓM CONFESSION & NOTIFICATION
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

        # 1.2 NHÓM QUOTE (TÁCH RIÊNG RA KHỎI NOTI)
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
            # Nếu dùng link chuyển hướng bình thường thay vì AJAX
            messages.success(request, "🔄 Đã cập nhật trạng thái quote.")
            return redirect(f"{request.path}?tab=quote")

        # 1.3 NHÓM RELAX & PANTRY (Giữ nguyên logic của bạn nhưng sửa thụt lề)
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

        # Mặc định sau khi xử lý xong Post cho Confession
        if current_tab == "confession":
            return redirect(f"{request.path}?tab=confession&filter={current_filter}")

    # --- PHẦN 2: CHUẨN BỊ DỮ LIỆU HIỂN THỊ (GET) ---
    posts = []
    reports = []
    health_configs = {}
    pantry_restaurants = []
    all_quotes = []

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
    }

    return render(request, "core/moderation.html", context)


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


def health_page(request):
    # 1. Lấy danh sách bài tập từ DB
    exercises_db = HealthExercise.objects.all()

    # Chuyển thành Dictionary để dễ dùng: {'yoga': <Object>, 'wrist': <Object>...}
    exercises = {ex.code: ex for ex in exercises_db}

    # 2. Dữ liệu mặc định (Nếu DB chưa có bài đó)
    default_data = {
        "yoga": "s-7lyvblFNI",
        "wrist": "QZjkZa4NxNg",
        "meditation": "O-6f5wQXSu8",
        "music": "jfKfPfyJRdk",
    }

    # 3. Danh sách câu nói truyền cảm hứng
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


@login_required
def shop_page(request):
    # 1. Lấy danh sách sản phẩm (Có thể phân loại theo danh mục)
    products = Product.objects.filter(is_active=True).order_by("-created_at")

    # 2. Xử lý logic Đổi quà bằng điểm KPI
    if request.method == "POST" and "redeem_product" in request.POST:
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        user_profile = request.user.profile

        # Kiểm tra xem đủ điểm không
        if user_profile.total_kpi_points >= product.price:
            # Trừ điểm và tạo lịch sử (PointHistory)
            user_profile.total_kpi_points -= product.price
            user_profile.save()

            # Gửi thông báo cho Admin hoặc User
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
