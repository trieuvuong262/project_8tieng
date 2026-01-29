from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    DailyQuote, UserProfile, PointHistory, RewardItem, 
    DocumentResource, FoodReview, Confession, Comment, 
    Product
)
from .models import PostReport # Import thêm model này

# --- TÙY CHỈNH HEADER ADMIN ---
admin.site.site_header = "8Tieng.vn Administration"
admin.site.site_title = "Quản trị Hệ sinh thái 8Tieng"
admin.site.index_title = "Dashboard Quản lý"

# --- 1. USER & PROFILE (Gộp Profile vào trong User) ---

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ 8Tieng (KPI & Rank)'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'get_kpi', 'get_company', 'is_staff')
    
    def get_kpi(self, instance):
        return instance.profile.total_kpi_points
    get_kpi.short_description = 'Điểm KPI'

    def get_company(self, instance):
        return instance.profile.company_name
    get_company.short_description = 'Công ty'

# Hủy đăng ký User cũ và đăng ký User mới đã kèm Profile
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# --- 2. GAMIFICATION ---

@admin.register(PointHistory)
class PointHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'amount_colored', 'created_at', 'description')
    list_filter = ('action_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at',)

    def amount_colored(self, obj):
        color = 'green' if obj.amount > 0 else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.amount)
    amount_colored.short_description = 'Điểm số'

@admin.register(RewardItem)
class RewardItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'point_cost', 'stock', 'image_preview')
    search_fields = ('title',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Ảnh'

# --- 3. ZONE 1: TÀI LIỆU ---

@admin.register(DocumentResource)
class DocumentResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'download_count', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'description')

# --- 4. ZONE 2: REVIEW ĂN UỐNG ---

@admin.register(FoodReview)
class FoodReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'rating_stars', 'avg_price_vnd', 'location_address')
    list_filter = ('rating',)
    
    def rating_stars(self, obj):
        return "⭐" * obj.rating
    rating_stars.short_description = 'Đánh giá'

    def avg_price_vnd(self, obj):
        return f"{obj.avg_price:,} đ"
    avg_price_vnd.short_description = 'Giá TB'

# --- 5. ZONE 3: CONFESSION (QUAN TRỌNG: Cần duyệt bài) ---

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Confession)
class ConfessionAdmin(admin.ModelAdmin):
    list_display = ('title_short', 'pseudonym', 'status_badge', 'created_at', 'likes_count')
    list_filter = ('status', 'is_anonymous', 'created_at')
    search_fields = ('content', 'pseudonym')
    actions = ['approve_confessions', 'reject_confessions']
    inlines = [CommentInline] # Xem comment ngay trong bài post

    def title_short(self, obj):
        return obj.title if len(obj.title) < 50 else obj.title[:50] + '...'
    title_short.short_description = 'Tiêu đề'

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Trạng thái'

    # Action: Duyệt bài nhanh
    def approve_confessions(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_confessions.short_description = "Duyệt các bài đã chọn"

    # Action: Từ chối bài nhanh
    def reject_confessions(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_confessions.short_description = "Từ chối các bài đã chọn"

# --- 6. ZONE 4: SHOPPING ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Thay 'title' bằng 'name' (theo đúng model)
    # Đảm bảo 'platform' có tồn tại trong model
    list_display = ('name', 'category', 'price_display', 'affiliate_url','is_hot') 
    
    # Đảm bảo 'platform' có trong model để filter
    list_filter = ('category', 'name','is_hot') 
    # --- 7. CONFIG ---


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_link', 'reason', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    
    def post_link(self, obj):
        return f"Bài #{obj.post.id}: {obj.post.content[:30]}..."

@admin.register(DailyQuote)
class DailyQuoteAdmin(admin.ModelAdmin):
    list_display = ('content', 'time_category', 'author', 'is_active')
    list_filter = ('time_category', 'is_active')
    list_editable = ('is_active',)