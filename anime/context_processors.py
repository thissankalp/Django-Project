from .data import GENRE_TABS


def user_profile(request):
    return {
        "nav_genres": GENRE_TABS,
        "search_query": request.GET.get("q", "").strip(),
    }
