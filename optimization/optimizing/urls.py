from django.urls import path
from .views import (
    LinkedInMessageUploadView, 
    CandidateSaveView, 
    MessageClassificationView,
    FilterLinkedinProfileByStatusView
)

urlpatterns = [
    # Upload messages for a specific LinkedIn profile
    path('messages/upload/', 
         LinkedInMessageUploadView.as_view(), 
         name='linkedin-message-upload'),
    
    # Save a new candidate
    path('candidate/save/', 
         CandidateSaveView.as_view(), 
         name='candidate-save'),
    
    # Classify a specific message
    path('messages/classify/<int:message_id>/', 
         MessageClassificationView.as_view(), 
         name='message-classification'),

    path('messages/filter/', 
         FilterLinkedinProfileByStatusView.as_view(), 
         name='messages/filter/'),
]