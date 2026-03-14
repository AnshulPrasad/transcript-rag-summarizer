from django.db import models
from django.contrib.auth.models import User


class QueryLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='queries'
    )
    query = models.TextField()
    answer = models.TextField()
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Query Log'
        verbose_name_plural = 'Query Logs'

    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"[{self.created_at.strftime('%d %b %Y %H:%M')}] {user_str}: {self.query[:60]}"