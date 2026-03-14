from django.contrib import admin
from django.utils.html import format_html
from .models import QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user_email', 'short_query', 'short_answer', 'tokens_used')
    list_filter = ('created_at',)
    search_fields = ('query', 'answer', 'user__email')
    readonly_fields = ('user', 'query', 'answer', 'tokens_used', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def user_email(self, obj):
        if obj.user:
            return format_html('<span style="color:#b5732a">{}</span>', obj.user.email)
        return 'Anonymous'
    user_email.short_description = 'User'

    def short_query(self, obj):
        return obj.query[:80] + '…' if len(obj.query) > 80 else obj.query
    short_query.short_description = 'Question'

    def short_answer(self, obj):
        return obj.answer[:100] + '…' if len(obj.answer) > 100 else obj.answer
    short_answer.short_description = 'Answer'

    def has_add_permission(self, request):
        return False