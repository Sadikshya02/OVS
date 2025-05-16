from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from .models import Election, Voter, Candidate, Vote
from functools import wraps
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

def login_required_session(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'voter_id' not in request.session:
            messages.error(request, "Please login to continue.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        citizenship_id = request.POST.get('citizenship_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        address = request.POST.get('address')
        password = request.POST.get('password')
        security_question = request.POST.get('security_question')
        security_answer = request.POST.get('security_answer')

        if Voter.objects.filter(citizenship_id=citizenship_id).exists():
            messages.error(request, "This Citizenship ID is already registered.")
            return render(request, 'register.html')

        if len(citizenship_id) < 6:
            messages.error(request, "Citizenship ID must be at least 6 characters.")
            return render(request, 'register.html')

        if not password:
            messages.error(request, "Password cannot be empty.")
            return render(request, 'register.html')

        Voter.objects.create(
            citizenship_id=citizenship_id,
            name=name,
            email=email,
            gender=gender,
            age=age,
            address=address,
            password=make_password(password),
            security_question=security_question,
            security_answer=make_password(security_answer),
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'register.html')

def login_view(request):
    if request.method == "POST":
        citizenship_id = request.POST.get("citizenship_id")
        password = request.POST.get("password")

        try:
            voter = Voter.objects.get(citizenship_id=citizenship_id)
            if check_password(password, voter.password):
                request.session['voter_id'] = voter.id
                request.session['voter_name'] = voter.name
                return redirect("vote")
            else:
                messages.error(request, "Invalid Citizenship ID or Password")
        except Voter.DoesNotExist:
            messages.error(request, "Invalid Citizenship ID or Password")

    return render(request, "login.html")

@login_required_session
def vote(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)

    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))

    # Find the active election (if any)
    current_election = Election.objects.filter(
        start_date__lte=now,
        end_date__gte=now
    ).first()

    # Find the most recent past election (if no active election)
    recent_election = Election.objects.filter(
        end_date__lt=now
    ).order_by('-end_date').first() if not current_election else None

    # Find upcoming elections
    upcoming_elections = Election.objects.filter(
        start_date__gt=now
    ).order_by('start_date')

    voting_allowed = False
    voting_message = ""
    election_time_range = "Voting time not set"

    if current_election:
        # Election is currently active
        voting_allowed = True
        voting_message = "🗳 Please cast your vote below"
        # Convert UTC times to Nepal time
        start_time = current_election.start_date.astimezone(pytz.timezone('Asia/Kathmandu'))
        end_time = current_election.end_date.astimezone(pytz.timezone('Asia/Kathmandu'))
        election_time_range = f"Voting from {start_time.strftime('%a, %b %d, %Y, %H:%M:%S')} to {end_time.strftime('%a, %b %d, %Y, %H:%M:%S')}"
        candidates = Candidate.objects.filter(election=current_election)
        election_context = current_election
    elif recent_election:
        # Show candidates from the most recent past election
        candidates = Candidate.objects.filter(election=recent_election)
        election_context = recent_election
        voting_message = "⛔ The election has ended. You can no longer vote."
        end_time = recent_election.end_date.astimezone(pytz.timezone('Asia/Kathmandu'))
        election_time_range = f"Election ended on {end_time.strftime('%a, %b %d, %Y, %H:%M:%S')}"
    else:
        # No active or past elections
        candidates = []
        election_context = None
        voting_message = "⚠ No active elections at this time."
        election_time_range = "Voting time not set"

    # Handle voting logic
    user_voted = False
    voted_candidate = None
    vote_status_message = voting_message

    if current_election:
        user_voted = Vote.objects.filter(
            voter=voter,
            candidate__election=current_election
        ).exists()
        if user_voted:
            voted_candidate = Vote.objects.filter(
                voter=voter,
                candidate__election=current_election
            ).first().candidate
            voting_allowed = False
            vote_status_message = f"✅ You have already voted for {voted_candidate.name} ({voted_candidate.party})."
    elif recent_election:
        user_voted = Vote.objects.filter(
            voter=voter,
            candidate__election=recent_election
        ).exists()
        if user_voted:
            voted_candidate = Vote.objects.filter(
                voter=voter,
                candidate__election=recent_election
            ).first().candidate
            vote_status_message = f"✅ You voted for {voted_candidate.name} ({voted_candidate.party}) in the {recent_election.name} election."

    if request.method == "POST" and voting_allowed and not user_voted:
        selected_candidate_id = request.POST.get("vote")
        if not selected_candidate_id:
            vote_status_message = "⚠ Please select a candidate before submitting."
        else:
            selected_candidate = get_object_or_404(Candidate, id=selected_candidate_id)
            if selected_candidate.election != current_election:
                vote_status_message = "⚠ This candidate is not part of the current election."
            else:
                Vote.objects.create(voter=voter, candidate=selected_candidate)
                user_voted = True
                voted_candidate = selected_candidate
                vote_status_message = f"🎉 Congrats! You voted for {selected_candidate.name} ({selected_candidate.party})"
                if voter.email:
                    try:
                        vote_time = now.strftime('%Y-%m-%d %I:%M %p NPT')
                        send_mail(
                            subject='Vote Confirmation - Online Voting System',
                            message=(f"Dear {voter.name},\n\n"
                                     f"You have successfully voted for {selected_candidate.name} ({selected_candidate.party}) "
                                     f"at {vote_time}.\n"
                                     "Thank you for participating in the election.\n\n"
                                     "Regards,\nElection Committee"),
                            from_email='your_email@gmail.com',
                            recipient_list=[voter.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print("Email sending failed:", e)

    # Enhanced debug logging
    print(f"Current Election: {current_election}")
    print(f"Recent Election: {recent_election}")
    print(f"Election Context: {election_context}")
    print(f"Candidates: {list(candidates)}")
    print(f"Voting Allowed: {voting_allowed}")
    print(f"Election Time Range: {election_time_range}")
    print(f"Raw Start Time (DB): {current_election.start_date if current_election else None}")
    print(f"Raw End Time (DB): {current_election.end_date if current_election else None}")
    print(f"Processed Start Time: {start_time if 'start_time' in locals() else None}")
    print(f"Processed End Time: {end_time if 'end_time' in locals() else None}")

    return render(request, 'vote.html', {
        "user": voter,
        "candidates": candidates,
        "user_voted": user_voted,
        "voted_candidate": voted_candidate,
        "vote_status_message": vote_status_message,
        "current_election": current_election,
        "recent_election": recent_election,
        "election_context": election_context,
        "upcoming_elections": upcoming_elections,
        "now": now,
        "voting_allowed": voting_allowed,
        "election_time_range": election_time_range,
    })


@login_required_session
def candidate_detail(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election = candidate.election if hasattr(candidate, 'election') and candidate.election else Election.objects.filter(name='Mayor Selection').first() or {
        'name': 'Mayor Selection',
        'date': '2025-05-15',
        'description': 'Election for selecting the mayor of the city.'
    }

    votes = [120, 85, 60, 45, 30]
    candidates_list = ['Subash Khatriwada', 'Ujjwal Mawadi', 'Yuyutsu', 'Someone', 'Hot Lemon']
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']

    plt.figure(figsize=(8, 6))
    plt.bar(candidates_list, votes, color=colors)
    plt.title(f'Voting Trends for {election["name"] if isinstance(election, dict) else election.name}')
    plt.xlabel('Candidates')
    plt.ylabel('Number of Votes')
    plt.xticks(rotation=45)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    os.makedirs('static/graphs', exist_ok=True)
    graph_path = f'static/graphs/candidate_{candidate_id}_voting_trends.png'
    plt.savefig(graph_path, bbox_inches='tight')
    plt.close()

    context = {
        'candidate': candidate,
        'election': election,
        'graph_url': f'/static/graphs/candidate_{candidate_id}_voting_trends.png',
    }
    return render(request, 'candidate_detail.html', context)

@login_required_session
def elections(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))
    elections = Election.objects.all().order_by('-start_date')  # Fetch all elections, ordered by start date (newest first)

    return render(request, 'elections.html', {
        "user": voter,
        "now": now,
        "elections": elections,
    })

@login_required_session
def election_detail(request, election_id):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    election = get_object_or_404(Election, id=election_id)
    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))
    candidates = Candidate.objects.filter(election=election)

    return render(request, 'election_detail.html', {
        "user": voter,
        "election": election,
        "candidates": candidates,
        "now": now,
    })

@login_required_session
def candidates(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))
    candidates = Candidate.objects.all()

    return render(request, 'candidates.html', {
        'user': voter,
        'candidates': candidates,
        'now': now,
    })

@login_required_session
def my_votes(request):
    voter_id = request.session.get('voter_id')
    try:
        voter = Voter.objects.get(id=voter_id)
        votes = Vote.objects.filter(voter=voter).order_by('-timestamp')
        now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))
    except Voter.DoesNotExist:
        messages.error(request, "Voter not found.")
        return redirect('vote')

    return render(request, 'my_votes.html', {
        'voter': voter,
        'votes': votes,
        'now': now,
    })

@login_required_session
def help_page(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))

    return render(request, 'help.html', {
        'user': voter,
        'now': now,
    })

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")

def about(request):
    return render(request, 'about.html')

def rules(request):
    return render(request, 'rules.html')

@login_required_session
def change_password(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    now = timezone.now().astimezone(pytz.timezone('Asia/Kathmandu'))

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('change_password')

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters!")
            return redirect('change_password')

        try:
            voter.password = make_password(new_password)
            voter.save()
            messages.success(request, "Password changed successfully!")
            return redirect('vote')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'change_password.html', {
        'user': voter,
        'now': now,
    })

def forgot_password(request):
    if request.method == 'POST':
        citizenship_id = request.POST.get('citizenship_id')
        provided_answer = request.POST.get('security_answer')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if citizenship_id and not provided_answer:
            try:
                voter = Voter.objects.get(citizenship_id=citizenship_id)
                security_question = voter.security_question
                if not security_question:
                    messages.error(request, "No security question set for this voter.")
                    return redirect('forgot_password')
                return render(request, 'forgot_password.html', {
                    'citizenship_id': citizenship_id,
                    'security_question': security_question,
                })
            except Voter.DoesNotExist:
                messages.error(request, "Voter with this Citizenship ID not found.")
                return redirect('forgot_password')
        
        elif provided_answer and new_password and new_password == confirm_password:
            try:
                voter = Voter.objects.get(citizenship_id=citizenship_id)
                if check_password(provided_answer, voter.security_answer):
                    voter.password = make_password(new_password)
                    voter.save()
                    messages.success(request, "Your password has been successfully reset.")
                    return redirect('login')
                else:
                    messages.error(request, "Incorrect answer to the security question.")
                    return redirect('forgot_password')
            except Voter.DoesNotExist:
                messages.error(request, "Voter with this Citizenship ID not found.")
                return redirect('forgot_password')
        else:
            messages.error(request, "Please ensure the passwords match and try again.")
            return redirect('forgot_password')

    return render(request, 'forgot_password.html')

@login_required_session
def election_results(request):
    candidates = Candidate.objects.annotate(vote_count=Count('vote__id'))
    candidate_names = [c.name for c in candidates]
    votes = [c.vote_count for c in candidates]

    return render(request, 'results.html', {
        'candidate_names': candidate_names,
        'votes': votes,
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Election, Voter, Candidate, Vote
from django.db.models import Count
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

# Existing views remain unchanged...

@login_required_session
def election_report(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    
    if not election.published:
        return render(request, 'unauthorized.html', {
            'message': 'Results are not yet published by the admin.'
        })

    # Election start date
    start_date = election.start_date

    # Number of candidates
    candidate_count = Candidate.objects.filter(election=election).count()

    # Number of voters who voted
    voter_count = Vote.objects.filter(candidate__election=election).values('voter').distinct().count()

    # Winner (candidate with the most votes)
    winner = Candidate.objects.filter(election=election).annotate(vote_count=Count('vote')).order_by('-vote_count').first()
    winner_name = winner.name if winner else "No winner yet"

    # Vote data for graph
    candidates = Candidate.objects.filter(election=election).annotate(vote_count=Count('vote'))
    candidate_names = [c.name for c in candidates]
    votes = [c.vote_count for c in candidates]

    # Generate line graph
    plt.figure(figsize=(10, 6))
    plt.plot(candidate_names, votes, marker='o', linestyle='-', color='b')
    plt.title(f'Vote Distribution for {election.name}')
    plt.xlabel('Candidates')
    plt.ylabel('Number of Votes')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)

    os.makedirs('static/graphs', exist_ok=True)
    graph_path = f'static/graphs/{election.id}_vote_distribution.png'
    plt.savefig(graph_path, bbox_inches='tight')
    plt.close()

    context = {
        'election': election,
        'start_date': start_date,
        'candidate_count': candidate_count,
        'voter_count': voter_count,
        'winner_name': winner_name,
        'graph_url': f'/static/graphs/{election.id}_vote_distribution.png',
    }
    return render(request, 'election_report.html', context)