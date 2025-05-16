from django.urls import path
from . import views

urlpatterns = [
    # Core Pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('rules/', views.rules, name='rules'),
    
    # Authentication and User Management
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    
    # Voting and Election
    path('vote/', views.vote, name='vote'),
    path('candidate/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'),
    path('election_results/', views.election_results, name='election_results'),
    path('election/<int:election_id>/', views.election_detail, name='election_detail'),
    path('candidates/', views.candidates, name='candidates'),  # Added    # Added
    path('my_votes/', views.my_votes, name='my_votes'),       # Added
    path('help/', views.help_page, name='help_page'), 
    path('election/<int:election_id>/report/', views.election_report, name='election_report'),        # Updated
]