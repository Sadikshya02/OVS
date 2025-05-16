from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password

class Election(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)

    def _str_(self):
        return self.name

class Voter(models.Model):
    citizenship_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    address = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    security_question = models.CharField(max_length=255, blank=True, null=True)
    security_answer = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        if len(self.citizenship_id) < 6:
            raise ValidationError("Citizenship ID must be greater than 6 digits.")
        if not self.citizenship_id.isdigit():
            raise ValidationError("Citizenship ID must contain only numeric characters.")

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_security_answer(self, raw_answer):
        self.security_answer = make_password(raw_answer)

    def check_security_answer(self, raw_answer):
        return check_password(raw_answer, self.security_answer)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.set_password(self.password)
        if self.security_answer and not self.security_answer.startswith("pbkdf2_sha256$"):
            self.set_security_answer(self.security_answer)
        super().save(*args, **kwargs)

    def _str_(self):
        return self.name

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    biography = models.TextField(blank=True, default='')
    platform = models.TextField(blank=True, default='')
    experience = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='candidate_images/', blank=True, null=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return self.name

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'candidate')

    def _str_(self):
        return f"{self.voter.name} voted for {self.candidate.name}"

class VotingTime(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def _str_(self):
        return f"Voting from {self.start_time} to {self.end_time}"