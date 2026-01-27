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
from django.contrib.admin.views.decorators import staff_member_required # Bảo mật: Chỉ Admin mới vào được
from django.http import JsonResponse
from django.db.models import Count
from django.db.models import F,OuterRef, Subquery,Prefetch # <--- Thêm import này
from .models import (
    Dish, Restaurant, UserProfile, PointHistory, ZoneConfig, 
    Confession, Comment,Reaction,CheckIn,  # <--- Thêm Comment vào đây
    DocumentResource, Product, FoodReview, Notification,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostReport, HiddenPost
OuterRef, Subquery

from django.core.paginator import Paginator
import requests # <--- Nhớ import thư viện này
from django.core.files.base import ContentFile
import urllib.request # Thư viện để tải ảnh từ DiceBear

def get_time_context():
    """
    Xác định ngữ cảnh dựa trên giờ hiện tại.
    Trả về: (mode_string, greeting_title, greeting_sub)
    """
    hour = datetime.now().hour
    
    if 5 <= hour < 9:
        return 'morning', 'Chào buổi sáng!', 'Hôm nay Deadline thế nào, đã sẵn sàng chiến đấu chưa?'
    elif 9 <= hour < 11 or 13 <= hour < 16:
        return 'work', 'Giờ làm việc tập trung', 'Tắt Facebook đi, làm xong sớm về sớm nào!'
    elif 11 <= hour < 13:
        return 'lunch', 'Nghỉ trưa thôi!', '11h30 rồi, chuẩn bị order cơm chưa?'
    elif 16 <= hour < 18:
        return 'chill', 'Sắp được về rồi!', 'Cố lên, chỉ còn một chút nữa thôi.'
    else:
        return 'chill', 'Tan làm rồi!', 'Về nhà nghỉ ngơi hoặc lượn lờ shop decor chút không?'

def get_random_pseudonym():
    """Tạo tên ẩn danh ngẫu nhiên cho Confession"""
    adjectives = ["Mèo", "Cá Mập", "Gấu", "Thỏ", "Sóc", "Cú", "Hổ"]
    nouns = ["Kế Toán", "IT", "Sale", "Marketing", "HR", "Intern", "Designer"]
    colors = ["Béo", "Cận", "Thông Thái", "Vui Vẻ", "Trầm Cảm", "Ngây Thơ"]
    
    return f"{random.choice(adjectives)} {random.choice(nouns)} {random.choice(colors)}"

# --- 2. MAIN VIEWS ---

def dashboard(request):
    # --- 1. LOGIC CHECK-IN (Giữ nguyên) ---
    widget_template = 'core/widgets/guest_widget.html'
    if request.user.is_authenticated:
        today = timezone.now().date()
        has_checked_in = CheckIn.objects.filter(user=request.user, date=today).exists()
        widget_template = 'core/widgets/stats_widget.html' if has_checked_in else 'core/widgets/checkin_widget.html'

    # --- 2. LOGIC MÓN ĂN & QUÁN ĂN (MỚI CẬP NHẬT) ---
    
    # A. Lấy danh sách quán ăn (Lấy 8 quán có rating cao nhất)
    # Nếu chưa có model Restaurant, bạn cần tạo hoặc dùng list giả lập bên dưới
    try:
        restaurants = Restaurant.objects.all().order_by('-rating')[:8]
    except:
        restaurants = [] # Tránh lỗi nếu chưa migrate DB

    # B. Lấy danh sách món ăn cho Vòng quay (Randomizer)
    # Ưu tiên lấy từ DB, nếu không có thì dùng list cứng
    try:
        dishes_db = list(Dish.objects.values_list('name', flat=True))
    except:
        dishes_db = []
        
    if dishes_db:
        food_list = dishes_db
    else:
        food_list = ['Cơm tấm sườn bì', 'Bún đậu mắm tôm', 'Phở bò tái nạm', 'Cơm gà xối mỡ', 'Healthy Salad', 'Bánh mì chảo', 'Mì ý sốt kem']
    
    # Chọn 1 món gợi ý hiển thị tĩnh (cho widget cũ)
    today_food = random.choice(food_list)
    
    # Chuyển list món ăn sang JSON để Javascript dùng cho vòng quay
    dishes_json = json.dumps(food_list)

    # --- 3. CÁC DATA KHÁC (Giữ nguyên & Bổ sung) ---
    office_tools = [
        {'name': 'PDF to Word', 'icon': 'file-text', 'desc': 'Miễn phí'},
        {'name': 'Tính lương', 'icon': 'calculator', 'desc': 'Gross -> Net'},
        {'name': 'AI Assistant', 'icon': 'bot', 'desc': 'Trợ lý ảo'},
        {'name': 'Nén ảnh', 'icon': 'image', 'desc': 'Giảm dung lượng'},
    ]

    # Decor items (Dữ liệu giả cho phần Shop Decor bên sidebar)
    decor_items = [
        {'name': 'Cây kim tiền', 'image': 'https://images.unsplash.com/photo-1599598425947-d3eb10787d65?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Đèn bàn Pixar', 'image': 'https://images.unsplash.com/photo-1533230536417-66c303f8a484?auto=format&fit=crop&w=300&q=80'},
    ]

    # Health Tip (Mẹo sức khỏe ngẫu nhiên)
    health_tips = [
        {'title': 'Quy tắc 20-20-20', 'content': 'Cứ 20 phút nhìn màn hình, hãy nhìn xa 20 feet (6m) trong 20 giây để bảo vệ mắt.'},
        {'title': 'Uống nước đúng cách', 'content': 'Đừng đợi khát mới uống. Hãy đặt một cốc nước ngay tại bàn làm việc.'},
        {'title': 'Tư thế ngồi chuẩn', 'content': 'Giữ lưng thẳng, màn hình ngang tầm mắt để tránh đau cổ vai gáy.'},
    ]
    health_tip = random.choice(health_tips)

    latest_confessions = Confession.objects.filter(status='APPROVED').select_related('author').order_by('-created_at')[:2]
    top_users = UserProfile.objects.select_related('user').order_by('-total_kpi_points')[:3]

    # Context truyền xuống template
    context = {
        'widget_template': widget_template,
        'today_food': today_food,       # Món gợi ý đơn lẻ
        'dishes_json': dishes_json,     # List món cho vòng quay JS (MỚI)
        'restaurants': restaurants,     # List quán ăn (MỚI)
        'office_tools': office_tools,
        'latest_confessions': latest_confessions,
        'top_users': top_users,
        'decor_items': decor_items,
        'health_tip': health_tip,
    }

    return render(request, 'core/dashboard.html', context)

@login_required
def daily_checkin(request):
    """
    Logic nút 'Điểm danh' (+10 điểm)
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check xem đã điểm danh chưa để tránh spam
    already_checked = PointHistory.objects.filter(
        user=request.user, 
        action_type='LOGIN', 
        created_at__gte=today_start
    ).exists()

    if not already_checked:
        # 1. Cộng điểm vào Profile
        profile = request.user.profile
        profile.total_kpi_points = F('total_kpi_points') + 10
        profile.save()
        
        # 2. Ghi lịch sử
        PointHistory.objects.create(
            user=request.user,
            action_type='LOGIN',
            amount=10,
            description=f"Điểm danh ngày {timezone.now().strftime('%d/%m')}"
        )
        messages.success(request, "Đã điểm danh! +10 điểm KPI.")
    else:
        messages.warning(request, "Hôm nay bạn đã điểm danh rồi!")

    return redirect('home')

# --- 3. ZONE 3 VIEWS (CONFESSION) ---

def confession_feed(request):
    """
    Hiển thị danh sách bài viết, xử lý đăng bài mới & bộ lọc
    """
    # --- A. XỬ LÝ ĐĂNG BÀI MỚI (POST) ---
    if request.method == 'POST' and 'submit_confession' in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để đăng bài.")
            return redirect('login')
            
        content = request.POST.get('content')
        custom_pseudo = request.POST.get('pseudonym')
        company_input = request.POST.get('company_name')
        
        # [MỚI] Lấy giá trị từ checkbox 'is_anonymous'
        # Nếu user tích chọn -> Trả về 'on' -> True
        # Nếu không tích -> Trả về None -> False
        is_anon_status = request.POST.get('is_anonymous') == 'on'

        if content:
            # LOGIC XỬ LÝ TÊN HIỂN THỊ
            if custom_pseudo and custom_pseudo.strip():
                final_name = custom_pseudo.strip()
                # (Tùy chọn) Nếu đã nhập tên giả thì tự động ép thành ẩn danh luôn cho an toàn
                # is_anon_status = True 
            else:
                final_name = request.user.username # Lấy tên user hiện tại

            # TẠO BÀI VIẾT
            Confession.objects.create(
                content=content,
                author=request.user,
                pseudonym=final_name,
                company_name=company_input,
                
                # [QUAN TRỌNG] Thay True bằng biến is_anon_status
                is_anonymous=is_anon_status, 
                
                status='PENDING'
            )
            messages.success(request, "Đã gửi bài viết! Vui lòng chờ Admin duyệt.")
        return redirect('confession_feed')

    # --- B. XỬ LÝ HIỂN THỊ DANH SÁCH (GET) ---
    
    # 1. Query cơ bản: Chỉ lấy bài ĐÃ DUYỆT
    base_query = Confession.objects.filter(status='APPROVED')

    # 2. Lọc bỏ các bài mà User hiện tại đã ẩn (HiddenPost)
    if request.user.is_authenticated:
        base_query = base_query.exclude(hiddenpost__user=request.user)

        # 3. Kỹ thuật Subquery: Kiểm tra xem User đã thả tim/phẫn nộ bài nào chưa
        # Để tô màu nút bấm ở Frontend
        user_reaction_subquery = Reaction.objects.filter(
            post=OuterRef('pk'),
            user=request.user
        ).values('reaction_type')[:1]

        base_query = base_query.annotate(
            current_user_reaction=Subquery(user_reaction_subquery)
        )

    # 4. Tối ưu Query (Prefetch Comments & Authors để tránh N+1 Query)
    # Lấy luôn comment và sắp xếp comment cũ nhất lên trước (hoặc tùy chọn)
    comments_prefetch = Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author').order_by('created_at')
    )
    base_query = base_query.select_related('author').prefetch_related(comments_prefetch)

    # 5. Xử lý Bộ lọc (Filter Tabs)
    filter_type = request.GET.get('filter', 'newest')
    
    if filter_type == 'top':
        confession_list = base_query.order_by('-loves_count')
    elif filter_type == 'drama':
        confession_list = base_query.order_by('-comments_count')
    else:
        confession_list = base_query.order_by('-created_at')

    # 2. Phân trang (Pagination Logic)
    paginator = Paginator(confession_list, 10) # 10 bài viết mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/confession_feed.html', {
        'confessions': page_obj, # Truyền page_obj thay vì list gốc
        'active_filter': filter_type
    })


# =========================================================
# 2. VIEW XỬ LÝ BÌNH LUẬN (COMMENT)
# =========================================================
def submit_comment(request, post_id):
    """
    Xử lý gửi bình luận (Hỗ trợ Ẩn danh & Trả lời)
    """
    if request.method == 'POST':
        post = get_object_or_404(Confession, id=post_id)
        content = request.POST.get('comment_content')
        parent_id = request.POST.get('parent_id')
        
        # LOGIC: Checkbox ẩn danh
        # Nếu checkbox được tích, giá trị gửi lên sẽ là 'on' (hoặc value bạn đặt)
        # Nếu không tích, nó sẽ là None
        is_anonymous_comment = request.POST.get('is_anonymous') == 'on'
        
        if content:
            parent_comment = None
            if parent_id:
                parent_comment = Comment.objects.filter(id=parent_id).first()

            # Tạo Comment
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent_comment,
                is_anonymous=is_anonymous_comment # Lưu trạng thái ẩn danh
            )
            
            # Tăng biến đếm comment của bài viết (Dùng F expression để tránh race condition)
            post.comments_count = F('comments_count') + 1
            post.save()
            
            # (Tùy chọn) Gửi thông báo cho chủ bài viết nếu có người comment
            # if post.author and post.author != request.user:
            #     Notification.objects.create(...)
            
    # Redirect lại đúng chỗ (dùng anchor # để nhảy tới bài viết vừa comment)
    return redirect(f'/social/?filter=newest#post-{post_id}') 

# =========================================================
# 3. CÁC API PHỤ TRỢ (REPORT, HIDE, REACT)
# =========================================================

@login_required
def api_report_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Confession, id=post_id)
        reason = request.POST.get('reason', 'Spam hoặc nội dung xấu')
        
        # Tạo báo cáo
        PostReport.objects.create(user=request.user, post=post, reason=reason)
        messages.success(request, "Đã gửi báo cáo cho Admin xem xét.")
        return redirect('confession_feed')

@login_required
def api_hide_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Confession, id=post_id)
        # Tạo record ẩn (get_or_create để tránh lỗi nếu bấm 2 lần)
        HiddenPost.objects.get_or_create(user=request.user, post=post)
        messages.success(request, "Đã ẩn bài viết này vĩnh viễn.")
        return redirect('confession_feed')
    

@login_required
def api_like_confession(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Confession, id=post_id)
        post.likes_count = F('likes_count') + 1
        post.save()
        
        # Lấy lại số like mới nhất để trả về cho Frontend
        post.refresh_from_db()
        return JsonResponse({'success': True, 'new_likes': post.likes_count})
    return JsonResponse({'success': False}, status=400)
@login_required
def api_react_confession(request, post_id, reaction_type):
    """
    reaction_type: 'LOVE' hoặc 'ANGRY'
    """
    if request.method == 'POST':
        post = get_object_or_404(Confession, id=post_id)
        user = request.user
        
        # Kiểm tra xem user đã react bài này chưa
        existing_reaction = Reaction.objects.filter(user=user, post=post).first()
        
        action = 'added' # added, removed, switched
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # 1. Nếu bấm lại cảm xúc cũ -> Gỡ bỏ (Toggle OFF)
                existing_reaction.delete()
                if reaction_type == 'LOVE':
                    post.loves_count = F('loves_count') - 1
                else:
                    post.angry_count = F('angry_count') - 1
                action = 'removed'
            else:
                # 2. Nếu bấm cảm xúc khác -> Đổi (Switch)
                # Trừ cái cũ
                if existing_reaction.reaction_type == 'LOVE':
                    post.loves_count = F('loves_count') - 1
                else:
                    post.angry_count = F('angry_count') - 1
                
                # Cộng cái mới
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                
                if reaction_type == 'LOVE':
                    post.loves_count = F('loves_count') + 1
                else:
                    post.angry_count = F('angry_count') + 1
                action = 'switched'
        else:
            # 3. Chưa có -> Tạo mới
            Reaction.objects.create(user=user, post=post, reaction_type=reaction_type)
            if reaction_type == 'LOVE':
                post.loves_count = F('loves_count') + 1
            else:
                post.angry_count = F('angry_count') + 1
        
        post.save()
        post.refresh_from_db()
        
        return JsonResponse({
            'success': True, 
            'action': action,
            'loves': post.loves_count,
            'angries': post.angry_count
        })
        
    return JsonResponse({'success': False}, status=400)

@staff_member_required(login_url='login')
def moderation_dashboard(request):
    """
    Dashboard quản trị tập trung:
    1. Duyệt bài (Pending)
    2. Quản lý bài đã đăng (Approved) - Gỡ/Phạt/Xóa Comment
    3. Xử lý báo cáo (Reports)
    4. Gửi thông báo hệ thống
    """
    
    # =========================================================
    # 1. XỬ LÝ POST ACTION (Hành động của Admin)
    # =========================================================
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- NHÓM A: XỬ LÝ TRẠNG THÁI BÀI VIẾT ---
        if action in ['approve', 'reject', 'delete_notify']:
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Confession, id=post_id)
            
            if action == 'approve':
                post.status = 'APPROVED'
                post.save()
                messages.success(request, f"✅ Đã duyệt bài #{post.id}")
                
            elif action == 'reject':
                post.status = 'REJECTED'
                post.save()
                messages.warning(request, f"🚫 Đã từ chối bài #{post.id}")
                
            elif action == 'delete_notify':
                # Gỡ bài đã duyệt & Gửi cảnh báo
                reason = request.POST.get('violation_reason', 'Vi phạm quy tắc cộng đồng.')
                post.status = 'REJECTED'
                post.save()
                
                # Gửi thông báo cho tác giả
                if post.author:
                    Notification.objects.create(
                        user=post.author,
                        title="⚠️ Bài viết của bạn đã bị gỡ",
                        content=f"Bài viết: '{post.content[:50]}...'\nLý do: {reason}",
                        notification_type='WARNING'
                    )
                messages.error(request, f"🔥 Đã gỡ bài #{post.id} và gửi cảnh báo.")

        # --- NHÓM B: XỬ LÝ BÌNH LUẬN ---
        elif action == 'delete_comment':
            comment_id = request.POST.get('comment_id')
            post_id_redirect = request.POST.get('post_id_redirect') # Để redirect về đúng tab
            
            comment = get_object_or_404(Comment, id=comment_id)
            reason = "Vi phạm quy tắc ứng xử."
            
            # Gửi thông báo cho người comment
            if comment.author:
                Notification.objects.create(
                    user=comment.author,
                    title="⚠️ Bình luận bị xóa",
                    content=f"Bình luận tại bài #{comment.post.id} bị xóa.\nNội dung: '{comment.content[:30]}...'",
                    notification_type='WARNING'
                )
            
            comment.delete()
            messages.success(request, "Đã xóa bình luận vi phạm.")

        # --- NHÓM C: XỬ LÝ BÁO CÁO (REPORT) ---
        elif action == 'resolve_report':
            report_id = request.POST.get('report_id')
            decision = request.POST.get('decision') # 'delete' hoặc 'ignore'
            report = get_object_or_404(PostReport, id=report_id)
            
            if decision == 'delete':
                # Admin ĐỒNG Ý với báo cáo -> Gỡ bài
                post = report.post
                post.status = 'REJECTED'
                post.save()
                
                # Gửi thông báo phạt user đăng bài
                if post.author:
                    Notification.objects.create(
                        user=post.author,
                        title="⚠️ Bài viết bị gỡ do bị báo cáo",
                        content=f"Bài viết của bạn bị gỡ do vi phạm: {report.reason}",
                        notification_type='WARNING'
                    )
                
                # Đánh dấu báo cáo đã xử lý
                report.is_resolved = True
                report.save()
                messages.success(request, f"Đã xử lý report #{report.id}: Gỡ bài thành công.")
                
            elif decision == 'ignore':
                # Admin BỎ QUA báo cáo -> Giữ bài
                report.is_resolved = True
                report.save()
                messages.info(request, f"Đã bỏ qua report #{report.id}.")

        # --- NHÓM D: GỬI THÔNG BÁO HỆ THỐNG (Notification Tool) ---
        elif action == 'send_notification':
            target_type = request.POST.get('target_type') # 'ALL' hoặc 'SINGLE'
            target_username = request.POST.get('target_username')
            title = request.POST.get('noti_title')
            content = request.POST.get('noti_content')
            noti_type = request.POST.get('noti_type', 'SYSTEM')

            if target_type == 'ALL':
                # Gửi cho TOÀN BỘ User (Dùng bulk_create để tối ưu tốc độ)
                users = User.objects.all()
                notis = [
                    Notification(user=u, title=title, content=content, notification_type=noti_type)
                    for u in users
                ]
                Notification.objects.bulk_create(notis)
                messages.success(request, f"📢 Đã gửi thông báo đến toàn bộ {users.count()} thành viên.")

            elif target_type == 'SINGLE':
                try:
                    user = User.objects.get(username=target_username)
                    Notification.objects.create(
                        user=user, title=title, content=content, notification_type=noti_type
                    )
                    messages.success(request, f"📨 Đã gửi thông báo đến user {target_username}.")
                except User.DoesNotExist:
                    messages.error(request, f"❌ Không tìm thấy user: {target_username}")

        # Redirect về lại đúng Tab hiện tại để admin không phải click lại
        current_tab = request.GET.get('tab', 'pending')
        return redirect(f"{request.path}?tab={current_tab}")

    # =========================================================
    # 2. CHUẨN BỊ DỮ LIỆU HIỂN THỊ (GET)
    # =========================================================
    current_tab = request.GET.get('tab', 'pending')
    
    posts = []
    reports = []

    # Query theo Tab
    if current_tab == 'approved':
        # Tab Đã duyệt: Lấy bài Approved
        # Prefetch comments để hiển thị trong popup mà không query nhiều lần
        posts = Confession.objects.filter(status='APPROVED') \
            .prefetch_related('comments__author') \
            .order_by('-created_at')
            
    elif current_tab == 'reports':
        # Tab Báo cáo: Lấy Report chưa xử lý
        reports = PostReport.objects.filter(is_resolved=False) \
            .select_related('post', 'user', 'post__author') \
            .order_by('-created_at')
            
    else:
        # Tab mặc định: Chờ duyệt (Pending)
        posts = Confession.objects.filter(status='PENDING').order_by('created_at')

    # Thống kê cho Badge (Đếm số lượng để hiện số đỏ trên tab)
    stats = {
        'pending': Confession.objects.filter(status='PENDING').count(),
        'approved': Confession.objects.filter(status='APPROVED').count(),
        'reports': PostReport.objects.filter(is_resolved=False).count()
    }

    return render(request, 'core/moderation.html', {
        'posts': posts,
        'reports': reports,
        'current_tab': current_tab,
        'stats': stats
    })

@login_required
def my_profile(request):
    user = request.user
    
    # --- 1. XỬ LÝ AN TOÀN CHO PROFILE (GIỮ NGUYÊN) ---
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user,
            total_kpi_points=100,
            level_rank='Thực tập sinh'
        )
        if user.is_superuser:
            profile.total_kpi_points = 99999
            profile.job_title = "Quản Trị Viên Hệ Thống"
            profile.save()

    # --- 2. [MỚI] XỬ LÝ ĐỔI AVATAR (POST) ---
    if request.method == 'POST':
        # A. Chọn Avatar có sẵn (Từ Modal)
        avatar_seed = request.POST.get('avatar_seed')
        if avatar_seed:
            try:
                # Tạo URL ảnh từ DiceBear API
                img_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={avatar_seed}"
                
                # Tải ảnh về server và lưu
                # Lưu ý: Cần import urllib.request và ContentFile ở đầu file
                with urllib.request.urlopen(img_url) as response:
                    img_content = response.read()
                    # Lưu file đè lên avatar cũ
                    profile.avatar.save(f"{avatar_seed}.svg", ContentFile(img_content), save=True)
                    messages.success(request, "Đã cập nhật Avatar mới!")
            except Exception as e:
                messages.error(request, f"Lỗi khi lưu avatar: {e}")

        # B. Tải ảnh từ máy tính (Nếu dùng input file)
        if 'avatar_upload' in request.FILES:
            profile.avatar = request.FILES['avatar_upload']
            profile.save()
            messages.success(request, "Đã tải ảnh lên thành công!")
            
        return redirect('my_profile')

    # --- 3. TÍNH HẠNG & LOGIC KHÁC (GIỮ NGUYÊN) ---
    points = profile.total_kpi_points
    rank = "Thực tập sinh"
    if points >= 1000: rank = "Nhân viên chính thức"
    if points >= 5000: rank = "Trưởng nhóm"
    if points >= 10000: rank = "Giám đốc"
    if user.is_superuser: rank = "Administrator (VIP)"

    if profile.level_rank != rank:
        profile.level_rank = rank
        profile.save()

    # --- 4. CHUẨN BỊ DỮ LIỆU CHO GIAO DIỆN ---
    notifications = user.notifications.all().order_by('-created_at')
    
    # Lấy tất cả bài viết để hiển thị ở tab "Bài viết của tôi"
    all_posts = Confession.objects.filter(author=user).order_by('-created_at')
    
    # Danh sách các lựa chọn Avatar (Seeds) để hiện trong Modal
    avatar_options = [
        'Felix', 'Aneka', 'Zoe', 'Jack', 'Bella', 
        'Bandit', 'Mimi', 'Tigger', 'Spooky', 'Bubba',
        'Cuddles', 'Whiskers', 'Peanut', 'Shadow', 'Midnight'
    ]

    context = {
        'profile': profile,
        'notifications': notifications,
        'my_posts': all_posts, # Dùng biến này cho loop bài viết ở giao diện mới
        'rank': rank,
        'avatar_options': avatar_options, # Truyền list avatar xuống template
    }
    
    # Lưu ý: Render đúng file template mới cập nhật giao diện
    return render(request, 'core/profile.html', context)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Mặc định là User thường (is_staff=False) đã do Django xử lý
        UserProfile.objects.create(
            user=instance,
            total_kpi_points=100, # Tặng 100 điểm chào sân
            level_rank='Thực tập sinh'
        )
# core/views.py

def register(request):
    """Trang đăng ký thành viên mới"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # User mới tạo mặc định is_staff=False (Quyền User thường)
            # Profile đã được tạo tự động bởi Signal ở trên
            
            # Đăng nhập luôn sau khi đăng ký
            login(request, user)
            messages.success(request, f"Chào mừng {user.username}! Bạn được tặng 100 điểm KPI làm vốn.")
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def daily_checkin(request):
    if request.method == 'POST':
        today = timezone.now().date()
        
        # Kiểm tra xem đã check-in chưa để tránh spam điểm
        checkin, created = CheckIn.objects.get_or_create(user=request.user, date=today)
        
        if created:
            # Cộng điểm KPI (Ví dụ: 10 điểm mỗi ngày)
            profile = request.user.profile
            profile.total_kpi_points += 10
            profile.save()
            messages.success(request, "Điểm danh thành công! +10 KPI Points 🚀")
        else:
            messages.info(request, "Bạn đã điểm danh hôm nay rồi.")
            
    return redirect('home')

#-------------------------------------------Ăn trưa-----------------------
def lunch_page(request):
    # =========================================================
    # 1. CẤU HÌNH & THAM SỐ
    # =========================================================
    API_KEY = '00600188ac064b66a7940d1ce0d3800a' # Key Geoapify
    
    # Lấy tham số
    lat_param = request.GET.get('lat')
    lon_param = request.GET.get('lon')
    radius_param = request.GET.get('radius', '1000')
    
    # Lấy số trang từ URL (Mặc định là trang 1)
    page_db_num = request.GET.get('page_db', 1)
    page_api_num = request.GET.get('page_api', 1)

    # Validate bán kính
    try:
        radius = int(radius_param)
        if radius < 500: radius = 500
        if radius > 10000: radius = 10000
    except:
        radius = 1000

    # Validate tọa độ
    if lat_param and lon_param:
        LAT = lat_param
        LON = lon_param
    else:
        LAT = '10.7716' 
        LON = '106.7044'

    # Tạo chuỗi tham số gốc để giữ lại khi chuyển trang (tránh mất toạ độ/bán kính)
    base_params = f"lat={LAT}&lon={LON}&radius={radius}"

    # =========================================================
    # 2. XỬ LÝ QUÁN NỔI BẬT (DATABASE)
    # =========================================================
    try:
        # Lấy toàn bộ dữ liệu thô từ DB
        db_all_list = Restaurant.objects.all().order_by('-rating')
    except:
        db_all_list = []

    # --- PHÂN TRANG DB ---
    # Mỗi trang hiện 4 quán
    paginator_db = Paginator(db_all_list, 8) 
    # Biến này vẫn tên là db_restaurants như cũ, nhưng giờ là Page Object
    db_restaurants = paginator_db.get_page(page_db_num)

    # =========================================================
    # 3. XỬ LÝ QUÁN GẦN ĐÂY (API GEOAPIFY)
    # =========================================================
    # Tăng limit lên 24 để có đủ dữ liệu chia thành 3 trang (3 trang x 8 quán)
    url = f"https://api.geoapify.com/v2/places?categories=catering.restaurant&filter=circle:{LON},{LAT},{radius}&bias=proximity:{LON},{LAT}&limit=24&apiKey={API_KEY}"
    
    api_list_raw = [] # List chứa dữ liệu thô từ API
    
    food_images = [
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80',
        'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=500&q=80',
        'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=500&q=80',
        'https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=500&q=80',
    ]

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            for feature in features:
                props = feature.get('properties', {})
                if not props.get('name'): continue

                res = {
                    'name': props.get('name'),
                    'address': props.get('address_line2', props.get('address_line1', 'Đang cập nhật')),
                    'rating': round(random.uniform(4.0, 5.0), 1),
                    'review_count': random.randint(20, 150),
                    'category': props.get('datasource', {}).get('raw', {}).get('cuisine', 'Món ngon'),
                    'image': {'url': random.choice(food_images)},
                    'url_foody': f"http://googleusercontent.com/maps.google.com/?q={props.get('lat')},{props.get('lon')}",
                    'is_google': True
                }
                api_list_raw.append(res)
    except Exception as e:
        print(f"Lỗi API: {e}")

    # --- PHÂN TRANG API ---
    # Mỗi trang hiện 8 quán
    paginator_api = Paginator(api_list_raw, 8)
    # Biến này vẫn tên là api_restaurants như cũ
    api_restaurants = paginator_api.get_page(page_api_num)

    # =========================================================
    # 4. DỮ LIỆU VÒNG QUAY
    # =========================================================
    try:
        dishes_db = list(Dish.objects.values_list('name', flat=True))
        # Lấy tên từ list thô (api_list_raw) để đầy đủ món cho vòng quay
        api_names = [r['name'] for r in api_list_raw]
        full_list = dishes_db + api_names
    except:
        full_list = []
        
    food_list = full_list if full_list else ['Cơm tấm', 'Phở bò', 'Bún chả', 'Mì Ý']
    dishes_json = json.dumps(food_list[:60]) 

    # =========================================================
    # 5. TRUYỀN DATA
    # =========================================================
    context = {
        'db_restaurants': db_restaurants,   # Page Object (Quán Admin)
        'api_restaurants': api_restaurants, # Page Object (Quán API)
        'dishes_json': dishes_json,
        'current_radius': radius,
        'base_params': base_params,         # Chuỗi tham số (lat,lon,radius) để dùng ở nút HTML
    }
    return render(request, 'core/lunch.html', context)