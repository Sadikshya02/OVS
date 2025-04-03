# from django.contrib import admin
from django.contrib import admin
from .models import Voter, Candidate, Vote

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('name','citizenship_id', 'gender','email', 'age', 'address')
    search_fields = ('name', 'email')
    list_filter = ('gender', 'age')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'timestamp')
    list_filter = ('candidate',)

# Register your models here.
