# from django.db import models
# from django.core.exceptions import ValidationError

# # Create your models here.
# from django.db import models

# class Voter(models.Model):
#     citizenship_id = models.CharField(max_length=20, unique=True)
#     name = models.CharField(max_length=100)
#     gender = models.CharField(max_length=10)
#     age = models.IntegerField()
#     address = models.CharField(max_length=255)
#     email = models.EmailField()

#     def clean(self):
#         # Ensure citizenship_id is greater than 6 digits
#         if len(self.citizenship_id) <= 6:
#             raise ValidationError('Citizenship ID must be greater than 6 digits.')

#     def __str__(self):
#         return self.name

# class Candidate(models.Model):
#     name = models.CharField(max_length=100)
#     party = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name

# class Vote(models.Model):
#     voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
#     candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.voter.name} voted for {self.candidate.name}"

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password


class Voter(models.Model):
    citizenship_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, blank=True, null=True)  # Optional field
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    address = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Securely store password

    def clean(self):
        # Ensure Citizenship ID has more than 6 digits
        if len(self.citizenship_id) < 6:
            raise ValidationError("Citizenship ID must be greater than 6 digits.")

    def set_password(self, raw_password):
        """Hashes and stores the password securely."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


    def _str_(self):
        return self.name

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)

    def _str_(self):
        return self.name

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.voter.name} voted for {self.candidate.name}"