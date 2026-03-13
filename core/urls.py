from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.farmer_login, name='login'),  # root redirects to login
    path('login/', views.farmer_login, name='login'),
    path('logout/', views.farmer_logout, name='logout'),

    # Dashboard with manual prediction & rural water distribution
    path('dashboard/', views.dashboard, name='dashboard'),

    # Automated irrigation action
    path('automate-irrigation/', views.automate_irrigation, name='automate_irrigation'),
]