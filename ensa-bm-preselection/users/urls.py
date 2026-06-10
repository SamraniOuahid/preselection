# users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, MeView, ChangePasswordView, LogoutView,
    VerifyEmailConfirmView, PasswordResetView, PasswordResetConfirmView
)

urlpatterns = [
    path('register/',        RegisterView.as_view(),       name='register'),
    path('login/',           LoginView.as_view(),          name='login'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='token_refresh'),
    path('logout/',          LogoutView.as_view(),         name='logout'),
    path('me/',              MeView.as_view(),             name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('verify-email-confirm/', VerifyEmailConfirmView.as_view(), name='verify_email_confirm'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]