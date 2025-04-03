from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
from django.db import models

class Voter(models.Model):
    citizenship_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    address = models.CharField(max_length=255)
    email = models.EmailField()

    def clean(self):
        # Ensure citizenship_id is greater than 6 digits
        if len(self.citizenship_id) <= 6:
            raise ValidationError('Citizenship ID must be greater than 6 digits.')

    def __str__(self):
        return self.name

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter.name} voted for {self.candidate.name}"

