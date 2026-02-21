import json
import urllib.error
import urllib.parse
import urllib.request

from django.contrib import messages
from django.contrib.auth import login
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse

from .data import GENRE_TABS
from .forms import ContactForm, SignUpForm
from .models import Profile

FALLBACK_ANIME = [
    {
        "title": "Skyline Blades",
        "tagline": "Neon rooftops, silent vows.",
        "reason": "Tight choreography, character-driven rivalries, and an uplifting theme of found family.",
        "genre": "Action",
        "seasons": "2 seasons",
        "rating": "9.1",
        "image_url": "",
        "genres": ["Action", "Drama"],
    },
    {
        "title": "Starlit Atelier",
        "tagline": "Brushes that bend time.",
        "reason": "A calm, inspiring story about creativity and healing with gorgeous art direction.",
        "genre": "Slice of Life",
        "seasons": "1 season",
        "rating": "8.6",
        "image_url": "",
        "genres": ["Slice of Life", "Fantasy"],
    },
    {
        "title": "Crimson Circuit",
        "tagline": "A rebellion powered by rhythm.",
        "reason": "High-energy music battles, a lovable crew, and a clever take on tech ethics.",
        "genre": "Sci-Fi",
        "seasons": "3 seasons",
        "rating": "9.0",
        "image_url": "",
        "genres": ["Sci-Fi", "Music"],
    },
    {
        "title": "Moonlit Courier",
        "tagline": "Deliveries across spirit realms.",
        "reason": "Soft fantasy with heartfelt episodic stories that always stick the landing.",
        "genre": "Fantasy",
        "seasons": "1 season",
        "rating": "8.8",
        "image_url": "",
        "genres": ["Fantasy", "Adventure"],
    },
]

FALLBACK_GENRES = [
    {"name": "Action", "count": 1200},
    {"name": "Adventure", "count": 980},
    {"name": "Comedy", "count": 870},
    {"name": "Drama", "count": 860},
    {"name": "Fantasy", "count": 820},
    {"name": "Romance", "count": 640},
]

ABOUT_POINTS = [
    "Anime is Japanese animation with distinctive art styles and storytelling.",
    "Genres range from action and fantasy to slice of life and romance.",
    "Shows are produced in seasons, often adapted from manga or original scripts.",
    "Great starter picks usually have shorter seasons and tight narratives.",
]

VERIFY_SALT = "anime-verify"
VERIFY_MAX_AGE = 60 * 60 * 24


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AnimeAtlas/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def shorten(text, max_length=160):
    if not text:
        return "A compelling series with strong visuals and memorable characters."
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1].rstrip()}…"


def build_anime_cards(items):
    cards = []
    for item in items:
        genres = [genre.get("name") for genre in item.get("genres", []) if genre.get("name")]
        season = item.get("season") or "Season"
        year = item.get("year") or ""
        season_text = f"{season.title()} {year}".strip()
        episodes = item.get("episodes") or "?"
        cards.append(
            {
                "title": item.get("title") or "Untitled",
                "tagline": item.get("title_english") or item.get("title_japanese") or "A standout series",
                "reason": shorten(item.get("synopsis")),
                "genre": genres[0] if genres else "Mixed",
                "genres": genres or ["Mixed"],
                "seasons": f"{episodes} eps • {season_text}".strip(),
                "rating": f"{item.get('score') or 'N/A'}",
                "image_url": item.get("images", {}).get("jpg", {}).get("image_url", ""),
            }
        )
    return cards


def _average_score(animes):
    scores = []
    for anime in animes:
        try:
            scores.append(float(anime.get("rating", 0)))
        except (TypeError, ValueError):
            continue
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _verification_token(user):
    return signing.dumps({"user_id": user.id}, salt=VERIFY_SALT)


def _verify_token(token):
    data = signing.loads(token, salt=VERIFY_SALT, max_age=VERIFY_MAX_AGE)
    return data.get("user_id")


def _send_verification_email(user, request):
    token = _verification_token(user)
    verify_url = request.build_absolute_uri(reverse("verify_email", args=[token]))
    subject = "Verify your Anime Atlas account"
    message = (
        "Welcome to Anime Atlas!\n\n"
        "Please verify your account by visiting this link:\n"
        f"{verify_url}\n\n"
        "If you did not sign up, you can ignore this email."
    )
    send_mail(subject, message, None, [user.email], fail_silently=True)


def home(request):
    animes = FALLBACK_ANIME
    genres = FALLBACK_GENRES
    api_note = "Showing curated starter picks."
    search_query = request.GET.get("q", "").strip()

    try:
        if search_query:
            query = urllib.parse.quote(search_query)
            anime_data = fetch_json(f"https://api.jikan.moe/v4/anime?q={query}&limit=6")
            api_note = f"Search results for '{search_query}'."
        else:
            anime_data = fetch_json("https://api.jikan.moe/v4/top/anime?limit=6")
        genre_data = fetch_json("https://api.jikan.moe/v4/genres/anime?filter=genres")
        animes = build_anime_cards(anime_data.get("data", [])) or FALLBACK_ANIME
        genres = [
            {"name": item.get("name"), "count": item.get("count")}
            for item in genre_data.get("data", [])[:10]
            if item.get("name")
        ] or FALLBACK_GENRES
        if not search_query:
            api_note = "Live data powered by the Jikan anime API."
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        animes = FALLBACK_ANIME
        genres = FALLBACK_GENRES
        api_note = "Live data unavailable. Showing curated starter picks."
        if search_query:
            api_note = "Live data unavailable. Showing curated starter picks instead."

    metrics = [
        {"label": "Featured series", "value": str(len(animes))},
        {"label": "Genres highlighted", "value": str(len(genres))},
        {"label": "Average score", "value": f"{_average_score(animes):.1f}"},
        {"label": "Updated just now", "value": "Live"},
    ]

    highlights = [
        {
            "title": "Why people watch",
            "detail": "Bold character arcs, expressive visuals, and stories that mix heart with adrenaline.",
        },
        {
            "title": "Top mood",
            "detail": "Cinematic action blended with cozy, slice-of-life recovery moments.",
        },
        {
            "title": "Watch guide",
            "detail": "Start with shorter seasons, then move to long-running epics when you are ready.",
        },
    ]

    return render(
        request,
        "anime/home.html",
        {
            "animes": animes,
            "genres": genres,
            "metrics": metrics,
            "highlights": highlights,
            "about_points": ABOUT_POINTS,
            "api_note": api_note,
        },
    )


def dashboard(request):
    return render(
        request,
        "anime/dashboard.html",
        {
            "metrics": [],
            "highlights": [],
        },
    )


def genre_page(request, slug):
    genre = next((item for item in GENRE_TABS if item["slug"] == slug), None)
    if not genre:
        messages.error(request, "Genre not found.")
        return redirect("home")

    animes = FALLBACK_ANIME
    api_note = "Showing curated starter picks."

    try:
        anime_data = fetch_json(
            f"https://api.jikan.moe/v4/anime?genres={genre['id']}&order_by=score&sort=desc&limit=8"
        )
        animes = build_anime_cards(anime_data.get("data", [])) or FALLBACK_ANIME
        api_note = f"Live {genre['name']} titles powered by Jikan."
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        animes = FALLBACK_ANIME
        api_note = "Live data unavailable. Showing curated starter picks."

    return render(
        request,
        "anime/genre.html",
        {
            "genre": genre,
            "animes": animes,
            "api_note": api_note,
        },
    )


def about(request):
    return render(request, "anime/about.html", {"about_points": ABOUT_POINTS})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Thanks! Your message has been received.")
            return redirect("contact")
    else:
        form = ContactForm()

    return render(request, "anime/contact.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.save()
            _send_verification_email(user, request)
            login(request, user)
            messages.info(
                request,
                "Account created. Check the console email to verify your account.",
            )
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "anime/signup.html", {"form": form})


def verify_email(request, token):
    try:
        user_id = _verify_token(token)
    except signing.BadSignature:
        messages.error(request, "Verification link is invalid or expired.")
        return redirect("home")

    profile = Profile.objects.filter(user_id=user_id).first()
    if not profile:
        messages.error(request, "Account not found.")
        return redirect("home")

    if profile.is_verified:
        messages.info(request, "Your account is already verified.")
    else:
        profile.is_verified = True
        profile.save()
        messages.success(request, "Your account is verified. Welcome!")

    return redirect("home")
