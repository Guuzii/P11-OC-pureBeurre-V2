from django.contrib import admin

# Register your models here.
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "product", "date", "is_validated")
    list_filter = ("is_validated", "date")
    search_fields = ("user.first_name", "user.last_name", "user.email", "message")
    actions = ["approve_comments"]

    def approve_comments(self, request, queryset):
        queryset.update(is_validated=True)
