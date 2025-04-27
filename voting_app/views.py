from django.shortcuts import render, redirect
from .models import Voter, Candidate, Vote
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
def index(request):
    return render(request, 'index.html')
# Comments
# Hello 
def register(request):
    if request.method == 'POST':
        # Get form data manually from the POST request
        citizenship_id = request.POST.get('citizenship_id')
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        address = request.POST.get('address')
        email = request.POST.get('email')

        # Check if the citizenship_id already exists
        if Voter.objects.filter(citizenship_id=citizenship_id).exists():
            messages.error(request, "This Citizenship ID is already registered.")
            return render(request, 'register.html')

        # Check if the citizenship_id is greater than 6 digits
        if len(citizenship_id) <= 6:
            messages.error(request, "Citizenship ID must be greater than 6 digits.")
            return render(request, 'register.html')

        # Create and save the Voter object
        Voter.objects.create(
            citizenship_id=citizenship_id,
            name=name,
            gender=gender,
            age=age,
            address=address,
            email=email
        )

        # After successful registration, redirect to login
        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'register.html')

@login_required(login_url='login')  # Redirects to login page if user is not authenticated
def vote(request):
    candidates = Candidate.objects.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please login to vote.")  # Display error message
            return redirect('login')  # Redirect to login page

        selected_candidate_id = request.POST.get('vote')
        if selected_candidate_id:
            selected_candidate = Candidate.objects.get(id=selected_candidate_id)
            Vote.objects.create(user=request.user, candidate=selected_candidate)
            messages.success(request, "Your vote has been submitted successfully!")
            return redirect('vote')  # Redirect after voting

    return render(request, 'vote.html', {'candidates': candidates})

def login_view(request):
    if request.method == "POST":
        citizenship_id = request.POST.get("citizenship_id")
        password = request.POST.get("password")

        try:
            voter = Voter.objects.get(citizenship_id=citizenship_id)
        except Voter.DoesNotExist:
            messages.error(request, "Invalid Citizenship ID or Password")
            return redirect("login")

        user = authenticate(request, username=voter.user.username, password=password)

        if user is not None:
            login(request, user)
            return redirect("vote")  # Redirect to vote page after successful login
        else:
            messages.error(request, "Invalid Citizenship ID or Password")

    return render(request, "login.html")

def about(request):
    return render(request, 'about.html')

def rules(request):
    return render(request, 'rules.html')
