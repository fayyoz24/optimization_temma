import os
import pandas as pd
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import openai
from django.conf import settings

from .models import LinkedInProfile, ProfileStatus, Candidate, LinkedInMessage
from .serializers import (
    LinkedInProfileSerializer, 
    ProfileStatusSerializer, 
    CandidateSerializer,
    LinkedInMessageSerializer
)

# Configure OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

import os
import pandas as pd
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import openai
from django.conf import settings

from .models import LinkedInProfile, ProfileStatus, LinkedInMessage

statuses_json = {
  "3.1": "Candidate is not interested in the mentorship program and asks no further question",
  "3.2": "Candidate is interested in the mentorship program and asks no further question",
  "3.2.1": "Candidate sends his or her WhatsApp number but asks no further question",
  "3.2.1.1": "Candidate shares his or her phone number and also asks some question",
  "3.3": "Candidate only asks further information but hasn't indicated any interest or not and provided no phone number",
  "3.4": "Candidate needs more information but he/she is already interested",
  "3.5": "Message cannot be classified",
  "3.6": "Candidate asks about payment",
  "3.7": "Candidate asks about Dutch language requirement",
  "3.8": "Candidate asks about Min-OCW involvement",
  "3.9": "Candidate thinks this is a questionnaire/survey",
  "3.12": "Candidate says they’re available only after a specific date",
  "3.13": "Candidate confirms they’ve already participated in the program",
  "3.14": "Candidate is concerned about the privacy or hesitates to participate because of that",
  "4.15": "Candidate indicates that he or she has responded late"
}

class LinkedInMessageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            # Configure OpenAI API key
            api_key = "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"

            from openai import OpenAI

            # Check if file was uploaded
            if 'file' not in request.FILES:
                return Response({"detail": "Messages Excel file is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            
            # Read Excel file
            messages_df = pd.read_excel(file)
            
            # Validate required column
            if 'last_message_content' not in messages_df.columns:
                return Response(
                    {"detail": "Excel file must contain 'last_message_content' column"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process messages
            messages_processed = []
            for _, row in messages_df.iterrows():
                message_text = row['last_message_content']
                profile_id = row['participants/1/url']
                profile_id = '123456'  # Temporary profile ID
                profile, _ = LinkedInProfile.objects.get_or_create(profile_id=profile_id)
                
                # Skip empty messages
                if pd.isna(message_text) or str(message_text).strip() == '':
                    continue
                
                # Create message entry
                message = LinkedInMessage.objects.create(
                    profile=profile,
                    message_text=str(message_text),
                    sent_date=datetime.now(),
                    is_incoming=True  # Default to incoming
                )
                
                # Classify message using OpenAI
                try:
            
                    # Prepare prompt for OpenAI
                    prompt = f"""
                    You are a classifier for LinkedIn messages. Given a message from a candidate, choose the **best matching** category **only** from the list below by returning the **status key** (e.g., "3.2.1").

                    Categories:
                    {json.dumps(statuses_json, indent=2)}

                    Message to classify:
                    \"\"\"{message.message_text}\"\"\"

                    Return ONLY the most appropriate status key (e.g., "3.1.1"). Do not include any explanation.
                    """

                    
                    # Call OpenAI API
                    response = openai.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[
                            {"role": "system", "content": "You are a message classifier for LinkedIn interactions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=10
                    )
                    
                    # Extract classification
                    classification = response.choices[0].message.content.strip()
                    
                    status_code = classification
                    
                    # Update message and create profile status
                    message.classified_status = status_code
                    message.save()

                    # Create profile status
                    ProfileStatus.objects.create(
                        profile=profile,
                        status=status_code,
                    )
                    
                    messages_processed.append({
                        'message_id': message.id,
                        'message_text': message.message_text,
                        'classified_status': status_code
                    })
                
                except Exception as classification_error:
                    # If classification fails, mark as unclassified
                    message.classified_status = '3.5'
                    message.save()
                    
                    ProfileStatus.objects.create(
                        profile=profile,
                        status='3.5',
                        datetime=datetime.now()
                    )
                    
                    messages_processed.append({
                        'message_id': message.id,
                        'message_text': message.message_text,
                        'classified_status': '3.5',
                        'classification_error': str(classification_error)
                    })
            
            return Response({
                "success": True,
                "profile": profile.name,
                "messages_processed": messages_processed,
                "total_messages": len(messages_processed)
            })
        
        except LinkedInProfile.DoesNotExist:
            return Response(
                {"detail": f"LinkedIn profile with ID {profile_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        # except Exception as e:
        #     return Response(
        #         {"detail": str(e), "success": False},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        

import os
import json
import pandas as pd
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from openai import OpenAI

class LinkedInMessageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            # Get OpenAI API key from environment variables or settings
            api_key = "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"
            
            if not api_key:
                return Response(
                    {"detail": "OpenAI API key not configured"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)

            # Check if file was uploaded
            if 'file' not in request.FILES:
                return Response(
                    {"detail": "Messages Excel file is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # participants/0/url
            file = request.FILES['file']
            
            # Read Excel file
            try:
                messages_df = pd.read_excel(file)
            except Exception as e:
                return Response(
                    {"detail": f"Error reading Excel file: {str(e)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate required columns
            required_columns = ['last_message_content', 'participants/1/url']
            missing_columns = [col for col in required_columns if col not in messages_df.columns]
            
            if missing_columns:
                return Response(
                    {"detail": f"Excel file must contain columns: {', '.join(missing_columns)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Define statuses for LinkedIn message classification
            statuses_json = {
                "3.1": "Candidate is not interested in the mentorship program and asks no further question",
                "3.2": "Candidate is interested in the mentorship program and asks no further question",
                "3.2.1": "Candidate sends his or her WhatsApp number but asks no further question",
                "3.2.1.1": "Candidate shares his or her phone number and also asks some question",
                "3.3": "Candidate only asks further information but hasn't indicated any interest or not and provided no phone number",
                "3.4": "Candidate needs more information but he/she is already interested",
                "3.5": "Message cannot be classified",
                "3.6": "Candidate asks about payment",
                "3.7": "Candidate asks about Dutch language requirement",
                "3.8": "Candidate asks about Min-OCW involvement",
                "3.9": "Candidate thinks this is a questionnaire/survey",
                "3.12": "Candidate says they're available only after a specific date",
                "3.13": "Candidate confirms they've already participated in the program",
                "3.14": "Candidate is concerned about the privacy or hesitates to participate because of that",
                "4.15": "Candidate indicates that he or she has responded late"
            }
            
            # Process messages
            messages_processed = []
            errors = []
            
            for index, row in messages_df.iterrows():
                try:
                    message_text = row['last_message_content']
                    profile_id = str(row['participants/1/url']) if not pd.isna(row['participants/1/url']) else '123456'
                    
                    # Skip empty messages
                    if pd.isna(message_text) or str(message_text).strip() == '':
                        continue
                    
                    # Get or create profile
                    profile, created = LinkedInProfile.objects.get_or_create(
                        profile_id=profile_id,
                        defaults={'name': f'Profile_{profile_id}'}  # Add default name
                    )
                    
                    # Create message entry
                    message = LinkedInMessage.objects.create(
                        # profile=profile,
                        message_text=str(message_text),
                        sent_date=datetime.now(),
                        is_incoming=True
                    )
                    
                    # Classify message using OpenAI
                    try:
                        # Prepare prompt for OpenAI
                        prompt = f"""
You are a classifier for LinkedIn messages about a mentorship program. Given a message from a candidate, choose the **best matching** category **only** from the list below by returning the **status key** (e.g., "3.2.1").

Categories:
{json.dumps(statuses_json, indent=2)}

Message to classify:
\"\"\"{message.message_text}\"\"\"

Instructions:
- Read the message carefully and understand the candidate's intent
- Look for key indicators like interest level, questions asked, contact information shared
- Choose the most specific category that matches
- If multiple categories could apply, choose the most specific one
- If none fit well, use "3.5" (Message cannot be classified)

Return ONLY the most appropriate status key (e.g., "3.2.1"). Do not include any explanation.
"""
                        
                        # Call OpenAI API with proper client
                        response = client.chat.completions.create(
                            model="gpt-4-turbo",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are a message classifier for LinkedIn interactions."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=10,
                            temperature=0  # For consistent classification
                        )
                        
                        # Extract classification
                        classification = response.choices[0].message.content.strip().strip('"')
                        
                        # Validate classification is in our statuses
                        if classification not in statuses_json:
                            classification = '3.5'  # Default to unclassified
                        
                        status_code = classification
                        
                    except Exception as classification_error:
                        # If classification fails, mark as unclassified
                        status_code = '3.5'
                        errors.append({
                            'row': index + 1,
                            'error': f'Classification failed: {str(classification_error)}'
                        })
                    
                    # Update message
                    message.classified_status = status_code
                    message.save()

                    # Create profile status
                    ProfileStatus.objects.create(
                        profile=profile,
                        status=status_code,
                        datetime=datetime.now()
                    )
                    
                    messages_processed.append({
                        'message_id': message.id,
                        'profile_id': profile_id,
                        'message_text': message.message_text[:100] + '...' if len(message.message_text) > 100 else message.message_text,
                        'classified_status': status_code,
                        'status_description': statuses_json.get(status_code, 'Unknown')
                    })
                    
                except Exception as row_error:
                    errors.append({
                        'row': index + 1,
                        'error': str(row_error)
                    })
                    continue
            
            response_data = {
                "success": True,
                "messages_processed": messages_processed,
                "total_messages": len(messages_processed),
                "total_rows_in_file": len(messages_df)
            }
            
            if errors:
                response_data["errors"] = errors
                response_data["error_count"] = len(errors)
            
            return Response(response_data)
        
        except Exception as e:
            return Response(
                {"detail": f"Unexpected error: {str(e)}", "success": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CandidateSaveView(APIView):
    def post(self, request):
        try:
            # Extract candidate data from request
            profile_id = request.data.get('profile_id')
            name = request.data.get('name')
            email = request.data.get('email')
            study = request.data.get('study')
            
            # Validate required fields
            if not profile_id or not name:
                return Response(
                    {"detail": "Profile ID and name are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create LinkedIn profile
            profile, created = LinkedInProfile.objects.get_or_create(
                profile_id=profile_id,
                defaults={'name': name}
            )
            
            # Create or update candidate
            candidate, candidate_created = Candidate.objects.get_or_create(
                profile=profile,
                defaults={
                    'email': email,
                    'study': study
                }
            )
            
            # Update candidate if not newly created
            if not candidate_created:
                if email:
                    candidate.email = email
                if study:
                    candidate.study = study
                candidate.save()
            
            # Ensure initial status is set
            if not ProfileStatus.objects.filter(profile=profile).exists():
                ProfileStatus.objects.create(
                    profile=profile,
                    status='0',  # Initial "Nothing" status
                    datetime=datetime.now()
                )
            
            return Response({
                "success": True,
                "candidate_id": candidate.id,
                "created": candidate_created
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
            )



import json
class MessageClassificationView(APIView):
    def post(self, request, message_id):
        try:
            # Get the message
            message = LinkedInMessage.objects.get(id=message_id)
            
            # Prepare prompt for OpenAI
            prompt = f"""
            You are a classifier for LinkedIn messages. Given a message from a candidate, choose the **best matching** category **only** from the list below by returning the **status key** (e.g., "3.2.1").

            Categories:
            {json.dumps(statuses_json, indent=2)}

            Message to classify:
            \"\"\"{message.message_text}\"\"\"

            Return ONLY the most appropriate status key (e.g., "3.1.1"). Do not include any explanation.
            """

            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="GPT-4.1",
                messages=[
                    {"role": "system", "content": "You are a message classifier for LinkedIn interactions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10
            )
            
            # Extract classification
            classification = response.choices[0].message.content.strip()
            
            # Validate classification
            # valid_statuses = ['3.1', '3.2', '3.3', '3.4', '3.5']
            # status_code = classification if classification in valid_statuses else '3.5'
            status_code = classification
            
            # Update message and create profile status
            message.classified_status = status_code
            message.save()
            
            ProfileStatus.objects.create(
                profile=message.profile,
                status=status_code,
                datetime=datetime.now()
            )
            
            return Response({
                "success": True,
                "status_code": status_code
            })
        
        except LinkedInMessage.DoesNotExist:
            return Response(
                {"detail": "Message not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

# class FilterLinkedinProfileByStatusView(APIView):
#     def get(self, request):
#         try:
#             status_code = request.GET.get('status')
#             # Filter profiles by status
#             profiles = LinkedInMessage.objects.filter(
#                 classified_status=status_code
#             )
            
#             # Serialize profiles
#             serializer = LinkedInMessageSerializer(profiles, many=True)
            
#             return Response(serializer.data)
        
#         except Exception as e:
#             return Response(
#                 {"detail": str(e), "success": False}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        

import io
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

class FilterLinkedinProfileByStatusView(APIView):
    def get(self, request):
        try:
            # Get status from query parameters
            status_code = request.GET.get('status')
            
            # Filter messages by status with related profile data
            messages = LinkedInMessage.objects.filter(
                classified_status=status_code, is_replied=False
            ).select_related('profile')
            
            # Prepare data for DataFrame
            data = []
            for message in messages:
                data.append({
                    'LinkedIn Profile ID': message.profile.profile_id,
                    'Profile Name': message.profile.name,
                    'Classified Status': message.classified_status
                })
                message.is_replied = True
                message.save()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Create an in-memory CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            # Prepare the response
            output.seek(0)
            response = HttpResponse(
                output.getvalue(), 
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename=linkedin_profiles_{status_code}.csv'
            return response
        
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
            )