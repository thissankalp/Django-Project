from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    mal_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    main_genre = models.CharField(max_length=64, blank=True)
    seasons = models.CharField(max_length=64, blank=True)
    genres_text = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True)
    rating = models.CharField(max_length=16, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "mal_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"
