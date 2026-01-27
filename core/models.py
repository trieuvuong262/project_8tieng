from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

# --- 0. UTILITIES & ABSTRACT MODELS (Lớp cơ sở) ---
# Dùng để tái sử dụng các trường chung, giúp DB gọn gàng

def get_file_path(instance, filename):
    """Hàm sinh đường dẫn file theo ngày: uploads/2023/10/25/filename"""
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.slug if hasattr(instance, 'slug') else timezone.now().timestamp(), ext)
    return os.path.join('uploads', timezone.now().strftime('%Y/%m/%d'), filename)

class BaseContent(models.Model):
    """Abstract Model chứa các trường chung cho tất cả bài đăng (Tài liệu, Review, Confession, Sản phẩm)"""
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name="URL Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")

    class Meta:
        abstract = True # Django sẽ không tạo bảng riêng cho class này

    def __str__(self):
        return self.title

# --- 1. USER & GAMIFICATION CLUSTER (Người dùng & Điểm thưởng) ---
class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(auto_now_add=True)
    # Có thể thêm time_out nếu muốn chấm công ra về
    
    class Meta:
        unique_together = ('user', 'date') # Một người chỉ check-in 1 lần/ngày

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Avatar")
    job_title = models.CharField(max_length=100, blank=True, verbose_name="Chức danh")
    company_name = models.CharField(max_length=100, blank=True, verbose_name="Công ty")
    
    # Gamification
    total_kpi_points = models.IntegerField(default=0, db_index=True, verbose_name="Tổng điểm KPI")
    level_rank = models.CharField(max_length=50, default='Intern', verbose_name="Cấp bậc") # Intern, Senior, Boss

    def __str__(self):
        return f"{self.user.username} - {self.job_title}"

class PointHistory(models.Model):
    """Lưu lịch sử biến động điểm để truy vết"""
    ACTION_CHOICES = [
        ('LOGIN', 'Điểm danh hàng ngày'),
        ('UPLOAD', 'Tải lên tài liệu'),
        ('POST', 'Viết bài/Review'),
        ('REDEEM', 'Đổi quà'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_histories')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.IntegerField(verbose_name="Số điểm (+/-)")
    description = models.CharField(max_length=255, verbose_name="Mô tả chi tiết")
    created_at = models.DateTimeField(auto_now_add=True)

class RewardItem(models.Model):
    """Kho quà đổi thưởng"""
    title = models.CharField(max_length=200, verbose_name="Tên phần quà")
    description = models.TextField(verbose_name="Mô tả")
    image = models.ImageField(upload_to='rewards/', verbose_name="Ảnh quà")
    point_cost = models.PositiveIntegerField(verbose_name="Điểm cần đổi")
    stock = models.PositiveIntegerField(default=10, verbose_name="Số lượng còn lại")
    
    def __str__(self):
        return f"{self.title} ({self.point_cost} pts)"

# --- 2. ZONE 1: PRODUCTIVITY (Bàn làm việc) ---

class DocumentResource(BaseContent):
    """Tài liệu mẫu, Slide, Excel"""
    FILE_TYPES = [
        ('PPT', 'PowerPoint'),
        ('XLS', 'Excel'),
        ('DOC', 'Word/PDF'),
        ('VECTOR', 'Design Vector'),
    ]
    description = models.TextField(blank=True, verbose_name="Mô tả tài liệu")
    file_upload = models.FileField(upload_to=get_file_path, verbose_name="File đính kèm")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='DOC')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Người upload")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Lượt tải")

    class Meta:
        verbose_name = "Tài liệu (Zone 1)"
        verbose_name_plural = "Kho Tài liệu"

# --- 3. ZONE 2: PANTRY & HEALTH (Ăn uống & Sức khỏe) ---

class FoodReview(BaseContent):
    """Review quán ăn trưa"""
    location_address = models.CharField(max_length=255, verbose_name="Địa chỉ")
    google_map_link = models.URLField(blank=True, verbose_name="Link Google Map")
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5, verbose_name="Đánh giá (Sao)")
    avg_price = models.PositiveIntegerField(help_text="Giá trung bình VND", verbose_name="Giá trung bình")
    cover_image = models.ImageField(upload_to='food/', verbose_name="Ảnh đại diện")
    
    # Lưu ý: Nếu cần nhiều ảnh, trong thực tế ta sẽ tạo thêm model FoodImage liên kết vào đây
    # Nhưng để đơn giản giai đoạn đầu, ta dùng 1 ảnh cover.

    class Meta:
        verbose_name = "Review Ăn uống (Zone 2)"
        verbose_name_plural = "Pantry Reviews"

# --- 4. ZONE 3: SOCIAL & DRAMA (Góc Trà Đá - Confession) ---

class Confession(BaseContent):
    """Bài viết ẩn danh"""
    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Từ chối'),
    ]
    
    content = models.TextField(verbose_name="Nội dung tâm sự")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    company_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Công ty liên quan")
    # Tính năng ẩn danh
    is_anonymous = models.BooleanField(default=True, verbose_name="Chế độ ẩn danh")
    pseudonym = models.CharField(max_length=100, verbose_name="Bút danh hiển thị") # Ví dụ: "Mèo Béo Kế Toán"
    loves_count = models.PositiveIntegerField(default=0, verbose_name="Lượt Yêu thích")
    angry_count = models.PositiveIntegerField(default=0, verbose_name="Lượt Phẫn nộ")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Lượt tim")
    comments_count = models.PositiveIntegerField(default=0, verbose_name="Lượt bình luận")

    class Meta:
        verbose_name = "Confession (Zone 3)"
        verbose_name_plural = "Danh sách Confessions"
        ordering = ['-created_at'] # Bài mới nhất lên đầu
class Notification(models.Model):
    TYPE_CHOICES = [
        ('SYSTEM', 'Hệ thống'),
        ('WARNING', 'Cảnh báo vi phạm'),
        ('SUCCESS', 'Tin vui'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thông báo cho {self.user.username}: {self.title}"
class Reaction(models.Model):
    REACTION_CHOICES = [
        ('LOVE', 'Yêu thích'),
        ('ANGRY', 'Phẫn nộ'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post') # 1 người chỉ được thả 1 cảm xúc cho 1 bài

# 3. CẬP NHẬT MODEL COMMENT (Thêm trả lời bình luận)
class Comment(models.Model):
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # TRƯỜNG MỚI
    is_anonymous = models.BooleanField(default=False, verbose_name="Bình luận ẩn danh")
    
    created_at = models.DateTimeField(auto_now_add=True)

# 2. MODEL BÁO CÁO VI PHẠM (REPORT)
class PostReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Người báo cáo
    post = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField(verbose_name="Lý do báo cáo")
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report by {self.user.username} on #{self.post.id}"

# 3. MODEL ẨN BÀI VIẾT (HIDDEN)
class HiddenPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_posts') # Người ẩn
    post = models.ForeignKey(Confession, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post') # 1 người chỉ ẩn 1 bài 1 lần
# --- 5. ZONE 4: SHOPPING (Shop Decor) ---

class Product(BaseContent):
    """Sản phẩm Affiliate"""
    PLATFORMS = [
        ('SHOPEE', 'Shopee'),
        ('LAZADA', 'Lazada'),
        ('TIKI', 'Tiki'),
        ('OTHER', 'Khác'),
    ]
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá bán")
    affiliate_link = models.URLField(verbose_name="Link mua hàng (Affiliate)")
    platform = models.CharField(max_length=20, choices=PLATFORMS, default='SHOPEE')
    image = models.ImageField(upload_to='products/', verbose_name="Ảnh sản phẩm")

    class Meta:
        verbose_name = "Sản phẩm (Zone 4)"
        verbose_name_plural = "Shop Decor"

# --- 6. SYSTEM CONFIG (Cấu hình hiển thị theo giờ) ---

class ZoneConfig(models.Model):
    """Cấu hình ưu tiên hiển thị cho Homepage"""
    ZONE_CHOICES = [
        ('ZONE_1', 'Bàn Làm Việc'),
        ('ZONE_2', 'Pantry & Health'),
        ('ZONE_3', 'Góc Trà Đá'),
        ('ZONE_4', 'Shop Decor'),
    ]
    
    zone_code = models.CharField(max_length=20, choices=ZONE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100, verbose_name="Tên hiển thị")
    icon_name = models.CharField(max_length=50, help_text="Tên icon Lucide (vd: coffee, briefcase)")
    color_class = models.CharField(max_length=50, help_text="Tailwind class (vd: bg-blue-50)")
    
    # Điểm ưu tiên hiển thị theo khung giờ (Thấp nhất = Hiển thị đầu tiên)
    priority_morning = models.IntegerField(default=0, verbose_name="Thứ tự Sáng")
    priority_work = models.IntegerField(default=0, verbose_name="Thứ tự Giờ làm")
    priority_lunch = models.IntegerField(default=0, verbose_name="Thứ tự Trưa")
    priority_chill = models.IntegerField(default=0, verbose_name="Thứ tự Chiều/Tối")

    def __str__(self):
        return self.display_name