from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),  # upload resume once
    path('update_profile/', views.update_profile, name='update_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),  # upload job description
    path('delete-analysis/<int:analysis_id>/', views.delete_analysis, name='delete_analysis'),  # delete analysis
    path('analysis-details/<int:analysis_id>/', views.get_analysis_details, name='get_analysis_details'),  # get analysis details
    path('debug-profile/', views.debug_profile, name='debug_profile'),  # debug endpoint
]
