from .data import GENRE_TABS
from .models import Profile


def user_profile(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
    else:
        profile = None

    return {
        "user_profile": profile,
        "nav_genres": GENRE_TABS,
        "search_query": request.GET.get("q", "").strip(),
    }
