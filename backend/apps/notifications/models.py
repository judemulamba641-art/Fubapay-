from django.db import models


class PushNotification(models.Model):
    notification_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    sent_at = models.DateTimeField()

    def __str__(self):
        return self.title