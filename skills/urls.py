from django.urls import path

from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/session-requests/<int:pk>/accept/', views.accept_session_request, name='accept_session_request'),
    path('dashboard/session-requests/<int:pk>/decline/', views.decline_session_request, name='decline_session_request'),
    path('skills/create/', views.skill_create, name='skill_create'),
    path('skills/<int:pk>/', views.skill_detail, name='skill_detail'),
    path('skills/<int:pk>/request-session/', views.request_session, name='request_session'),
    path('skills/<int:pk>/edit/', views.skill_update, name='skill_update'),
    path('skills/<int:pk>/delete/', views.skill_delete, name='skill_delete'),
]