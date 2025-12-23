from django.urls import path
from . import views

urlpatterns = [
    # CHANGE THIS LINE: point to views.index instead of views.login_view
    path('', views.index, name='index'), 
    
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_user, name='logout'),
    path('add-period/', views.add_period, name='add_period'),
    path('history/', views.history, name='history'),
    path('prediction/', views.prediction, name='prediction'),
    path('add-symptoms/', views.add_symptoms, name='add_symptoms'),
    path('reports/', views.reports, name='reports'),
]