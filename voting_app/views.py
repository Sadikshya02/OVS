
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Voter, Candidate, Vote
from functools import wraps
from django.core.mail import send_mail


# ----------------- Custom Login Decorator -----------------
def login_required_session(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'voter_id' not in request.session:
            messages.error(request, "Please login to continue.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# ----------------- Index -----------------
def index(request):
    return render(request, 'index.html')


# ----------------- Register -----------------
def register(request):
    if request.method == 'POST':
        citizenship_id = request.POST.get('citizenship_id')
        name = request.POST.get('name')
        email = request.POST.get('email')  
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        address = request.POST.get('address')
        password = request.POST.get('password')

        if Voter.objects.filter(citizenship_id=citizenship_id).exists():
            messages.error(request, "This Citizenship ID is already registered.")
            return render(request, 'register.html')

        if len(citizenship_id) < 6:
            messages.error(request, "Citizenship ID must be at least 6 characters.")
            return render(request, 'register.html')

        if not password:
            messages.error(request, "Password cannot be empty.")
            return render(request, 'register.html')

        hashed_password = make_password(password)

        Voter.objects.create(
            citizenship_id=citizenship_id,
            name=name,
            email=email,
            gender=gender,
            age=age,
            address=address,
            password=hashed_password,
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'register.html')


# ----------------- Login -----------------
def login_view(request):
    if request.method == "POST":
        citizenship_id = request.POST.get("citizenship_id")
        password = request.POST.get("password")

        try:
            voter = Voter.objects.get(citizenship_id=citizenship_id)
        except Voter.DoesNotExist:
            messages.error(request, "Invalid Citizenship ID or Password")
            return redirect("login")

        if check_password(password, voter.password):
            request.session['voter_id'] = voter.id
            request.session['voter_name'] = voter.name
            # messages.success(request, f"Welcome, {voter.name}!")
            return redirect("vote")
        else:
            messages.error(request, "Invalid Citizenship ID or Password")

    return render(request, "login.html")


# ----------------- Vote View -----------------
# @login_required_session
# def vote(request):
#     voter_id = request.session.get('voter_id')
#     voter = Voter.objects.get(id=voter_id)
#     candidates = Candidate.objects.all()

#     try:
#         user_vote = Vote.objects.get(voter=voter)
#         user_voted = True
#         voted_candidate = user_vote.candidate
#         vote_status_message = f"✅ You have already voted for {voted_candidate.name} ({voted_candidate.party})."
#     except Vote.DoesNotExist:
#         user_vote = None
#         user_voted = False
#         voted_candidate = None
#         vote_status_message = "🗳 Please cast your vote below"

#     if request.method == "POST" and not user_voted:
#         selected_candidate_id = request.POST.get("vote")
#         if not selected_candidate_id:
#             vote_status_message = "⚠️ Please select a candidate before submitting."
#         else:
#             selected_candidate = Candidate.objects.get(id=selected_candidate_id)
#             Vote.objects.create(voter=voter, candidate=selected_candidate)
#             user_voted = True
#             voted_candidate = selected_candidate
#             vote_status_message = f"🎉 Congrats! You voted for {selected_candidate.name} ({selected_candidate.party})"

#     return render(request, "vote.html", {
#         "user": voter,
#         "candidates": candidates,
#         "user_voted": user_voted,
#         "voted_candidate": voted_candidate,
#         "vote_status_message": vote_status_message,
#     })



@login_required_session
def vote(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(id=voter_id)
    candidates = Candidate.objects.all()

    try:
        user_vote = Vote.objects.get(voter=voter)
        user_voted = True
        voted_candidate = user_vote.candidate
        vote_status_message = f"✅ You have already voted for {voted_candidate.name} ({voted_candidate.party})."
    except Vote.DoesNotExist:
        user_vote = None
        user_voted = False
        voted_candidate = None
        vote_status_message = "🗳 Please cast your vote below"

    if request.method == "POST" and not user_voted:
        selected_candidate_id = request.POST.get("vote")
        if not selected_candidate_id:
            vote_status_message = "⚠️ Please select a candidate before submitting."
        else:
            selected_candidate = Candidate.objects.get(id=selected_candidate_id)
            Vote.objects.create(voter=voter, candidate=selected_candidate)
            user_voted = True
            voted_candidate = selected_candidate
            vote_status_message = f"🎉 Congrats! You voted for {selected_candidate.name} ({selected_candidate.party})"

            # ✅ Send email confirmation
            if voter.email:
                try:
                    send_mail(
                        subject='Vote Confirmation - Online Voting System',
                        message=(
                            f"Dear {voter.name},\n\n"
                            f"Thank you for voting in the Online Voting System.\n"
                            f"✅ You successfully voted for {selected_candidate.name} ({selected_candidate.party}).\n\n"
                            "This is a confirmation of your vote.\n\n"
                            "Regards,\n"
                            "Election Committee"
                        ),
                        from_email='your_email@gmail.com',  # Replace with your email
                        recipient_list=[voter.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print("Email sending failed:", e)

    return render(request, "vote.html", {
        "user": voter,
        "candidates": candidates,
        "user_voted": user_voted,
        "voted_candidate": voted_candidate,
        "vote_status_message": vote_status_message,
    })


# ----------------- Logout -----------------
def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


# ----------------- Other Pages -----------------
def about(request):
    return render(request, 'about.html')

def rules(request):
    return render(request, 'rules.html')

from django.db.models import Count
from .models import Candidate

def election_results(request):
    candidates = Candidate.objects.annotate(vote_count=Count('vote'))
    candidate_names = [c.name for c in candidates]
    votes = [c.vote_count for c in candidates]

    return render(request, 'results.html', {
        'candidate_names': candidate_names,
        'votes': votes,
    })
