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
                profile_id = row['profile_id']
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
                        Indicate which of the following classes does the message belong to. Just tell me the number:
                        3.1: he is not interested, 
                        3.2: he is interested, 
                        3.2.1: he sends his email address, 
                        3.3: he needs more information, 
                        3.4: he is interested while also needs more information, 
                        3.5: none of the above.

                        Please Response just a status code!!!
                    """
                    
                    from openai import OpenAI
                    api_key = "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"
                    client = OpenAI(api_key=api_key)

                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a message classification assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    # Extract classification
                    classification = completion.choices[0].message.content.strip()
                    
                    # Validate classification
                    # valid_statuses = ['0', '3.1', '3.2', '3.3', '3.4', '3.5']
                    status_code = classification
                    # status_code = classification if classification in valid_statuses else '3.5'
                    
                    # Update message with classification
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
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

class LinkedInMessageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            # Check if file was uploaded
            if 'file' not in request.FILES:
                return Response({"detail": "Messages Excel file is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            
            # Read Excel file
            messages_df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['last_message_content', 'last_message_who', 'last_message_date', 'participants/1/url']
            for col in required_columns:
                if col not in messages_df.columns:
                    return Response(
                        {"detail": f"Excel file must contain '{col}' column"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Process messages
            messages_processed = []
            for _, row in messages_df.iterrows():
                # Only process messages not sent by you
                if row['last_message_who'] == 'you':
                    continue
                
                message_text = row['last_message_content']
                profile_id = row['participants/1/url']
                sent_date = row['last_message_date']
                
                # Skip empty messages
                if pd.isna(message_text) or str(message_text).strip() == '':
                    continue
                
                # Get or create profile
                try:
                    profile = LinkedInProfile.objects.get(profile_id=profile_id)
                except LinkedInProfile.DoesNotExist:
                    # Optionally create profile if it doesn't exist
                    profile = LinkedInProfile.objects.create(
                        profile_id=profile_id,
                        name=row.get('participants/1/firstname', '') + ' ' + row.get('participants/1/lastname', '')
                    )
                
                # Create message entry
                message = LinkedInMessage.objects.create(
                    profile=profile,
                    message_text=str(message_text),
                    last_message_date=sent_date,
                    is_incoming=True
                )
                
                # Classify message using OpenAI (optional)
                try:
                    prompt = f"""
                        Indicate which of the following classes does the message belong to. Just tell me the number:
                        3.1: he is not interested, 
                        3.2: he is interested, 
                        3.2.1: he sends his email address, 
                        3.3: he needs more information, 
                        3.4: he is interested while also needs more information, 
                        3.5: none of the above.

                        Please Response just a status code!!!
                    """
                    
                    from openai import OpenAI
                    api_key = "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"
                    client = OpenAI(api_key=api_key)

                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a message classification assistant."},
                            {"role": "user", "content": prompt + "\n\nMessage: " + str(message_text)}
                        ]
                    )
                    
                    # Extract classification
                    classification = completion.choices[0].message.content.strip()
                    
                    # Update message with classification
                    message.classified_status = classification
                    message.save()
                    
                    # Create profile status
                    ProfileStatus.objects.create(
                        profile=profile,
                        status=classification,
                        datetime=sent_date
                    )
                    
                    messages_processed.append({
                        'message_id': message.id,
                        'message_text': message.message_text,
                        'classified_status': classification
                    })
                
                except Exception as classification_error:
                    # If classification fails, mark as unclassified
                    message.classified_status = '3.5'
                    message.save()
                    
                    ProfileStatus.objects.create(
                        profile=profile,
                        status='3.5',
                        datetime=sent_date
                    )
                    
                    messages_processed.append({
                        'message_id': message.id,
                        'message_text': message.message_text,
                        'classified_status': '3.5',
                        'classification_error': str(classification_error)
                    })
            
            return Response({
                "success": True,
                "messages_processed": messages_processed,
                "total_messages": len(messages_processed)
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
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

class MessageClassificationView(APIView):
    def post(self, request, message_id):
        try:
            # Get the message
            message = LinkedInMessage.objects.get(id=message_id)
            
            # Prepare prompt for OpenAI
            prompt = f"""Classify the message into one of these categories:
            3.1: Not interested
            3.2: Interested
            3.3: Needs more information
            3.4: Interested but needs more information
            3.5: Cannot be classified
            
            Message: {message.message_text}
            
            Respond with ONLY the status number."""
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
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
                    # 'Last Message Date': message.last_message_date,
                    'Classified Status': message.classified_status
                })
                message.is_replied=True
                message.save()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Create an in-memory Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='LinkedIn Profiles')
                
                # Auto-adjust columns width
                worksheet = writer.sheets['LinkedIn Profiles']
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + i)].width = column_len
            
            # Prepare the response
            output.seek(0)
            response = HttpResponse(
                output.read(), 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=linkedin_profiles_{status_code}.xlsx'
            return response
        
        except Exception as e:
            return Response(
                {"detail": str(e), "success": False}, 
                status=status.HTTP_400_BAD_REQUEST
            )