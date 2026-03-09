from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("genres/<slug:slug>/", views.genre_page, name="genre_page"),
    path("watchlist/", views.wishlist_list, name="watchlist"),
    path("watchlist/add/", views.wishlist_add, name="watchlist_add"),
    path("watchlist/<int:pk>/remove/", views.wishlist_remove, name="watchlist_remove"),
    path("anime/<int:mal_id>/", views.anime_detail, name="anime_detail"),
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="anime/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
