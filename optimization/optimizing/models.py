from django.db import models
from django.utils import timezone

class LinkedInProfile(models.Model):
    profile_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    # url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProfileStatus(models.Model):
    STATUS_CHOICES = [
        ('0', 'Nothing'),
        ('1', 'Listed as candidate to contact'),
        ('2', 'Introduction message sent'),
        ('3.1', 'Not interested'),
        ('3.2', 'Interested'),
        ('3.3', 'Needs more information'),
        ('3.4', 'Interested with more info needed'),
        ('3.5', 'Unclassified'),
    ]
    
    profile = models.ForeignKey(LinkedInProfile, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    datetime = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-datetime']

    def __str__(self):
        return f"{self.profile.name} - {self.get_status_display()}"

class Candidate(models.Model):
    profile = models.OneToOneField(LinkedInProfile, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)
    study = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Candidate: {self.profile.name}"

class LinkedInMessage(models.Model):
    profile = models.ForeignKey(LinkedInProfile, on_delete=models.CASCADE, related_name='messages')
    message_text = models.TextField()
    last_message_date = models.DateTimeField(null=True, blank=True)
    is_incoming = models.BooleanField(default=True)
    classified_status = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_replied = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_message_date']

    def __str__(self):
        return f"Message from {self.profile.name} at {self.last_message_date}"
    