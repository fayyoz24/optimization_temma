from rest_framework import serializers
from .models import LinkedInProfile, ProfileStatus, Candidate, LinkedInMessage

class LinkedInProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedInProfile
        fields = ['id', 'profile_id', 'name', 'url', 'created_at', 'updated_at']

class ProfileStatusSerializer(serializers.ModelSerializer):
    profile_name = serializers.ReadOnlyField(source='profile.name')
    
    class Meta:
        model = ProfileStatus
        fields = ['id', 'profile', 'profile_name', 'status', 'datetime']

class CandidateSerializer(serializers.ModelSerializer):
    profile_details = LinkedInProfileSerializer(source='profile', read_only=True)
    
    class Meta:
        model = Candidate
        fields = ['id', 'profile', 'profile_details', 'email', 'study', 'notes', 'created_at', 'updated_at']

class LinkedInMessageSerializer(serializers.ModelSerializer):
    profile_name = serializers.ReadOnlyField(source='profile.name')
    
    class Meta:
        model = LinkedInMessage
        fields = ['id', 'profile', 'profile_name', 'message_text', 'sent_date', 'is_incoming', 'classified_status', 'created_at']