from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.response import Response
from django.conf import settings
from ..models import Request, User_Request, Requirement, User
from ..serializers import RequestSerializer
from ..utilities import get_if_exists
import json
from django.core import serializers
import os

def index(request):
      all_requests = Request.objects.all()
      return render(request, 'user/request/index.html', {'all_requests': all_requests})

from django.contrib.auth import login, authenticate

def create_request(request):
    if request.method == 'POST':
        try:
            request_form = Request.objects.get(id=request.POST.get('id'))
            status = "Payment not yet settled"
            uploads = ""

            # Check if user is authenticated
            if request.user.is_authenticated:
                # Use the authenticated user
                user = request.user
            else:
                # For anonymous users, try to find user by email from session
                user_email = request.session.get('temp_user_email')
                user_password = request.session.get('temp_user_password')
            
                if not user_email:
                    return JsonResponse({'status': False, 'message': 'Profile information is required for unauthenticated users. Please register first.'})
            
                try:
                    # First try to get the user
                    user = User.objects.get(email=user_email)
                    
                    # Then authenticate with stored credentials
                    if user_password:
                        authenticated_user = authenticate(request, username=user_email, password=user_password)
                        if authenticated_user:
                            login(request, authenticated_user)
                            user = authenticated_user
                            print(f"User authenticated: {request.user.is_authenticated}")
                        else:
                            # Fallback to the old method if authentication fails
                            user.backend = 'django.contrib.auth.backends.ModelBackend'
                            login(request, user)
                            print(f"User authenticated (fallback): {request.user.is_authenticated}")
                    else:
                        # Fallback if no password in session
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        print(f"User authenticated (no password): {request.user.is_authenticated}")
                
                except User.DoesNotExist:
                    return JsonResponse({'status': False, 'message': 'User not found. Please register or login first.'})
        
            # Create user request
            user_request = User_Request(
                user=user,
                request=request_form,
                status=status,
                purpose=request.POST.get("purpose"),
                number_of_copies=int(request.POST.get("number_of_copies", 1))
            )
        
            # Update user type immediately if provided
            if 'user_type' in request.POST and user:
                user.user_type = int(request.POST.get('user_type'))
                user.save()
        
            # Store temp_user_info if available
            if 'temp_user_info' in request.POST:
                temp_user_info = json.loads(request.POST.get('temp_user_info'))
                user_request.temp_user_info = temp_user_info

            # Pre-save the object to get an ID
            user_request.save()

            # Create TempRecord if temp_user_info is available
            if hasattr(user_request, 'temp_user_info') and user_request.temp_user_info:
                from ..models import TempRecord
            
                # Create TempRecord entry
                temp_record = TempRecord(
                    user_request=user_request,
                    user_number=user.student_number,
                    first_name=temp_user_info.get('first_name', ''),
                    last_name=temp_user_info.get('last_name', ''),
                    middle_name=temp_user_info.get('middle_name', ''),
                    contact_no=temp_user_info.get('contact_no', ''),
                    course_code=temp_user_info.get('course', ''),
                    entry_year_from=int(temp_user_info.get('entry_year_from', 0)),
                    entry_year_to=int(temp_user_info.get('entry_year_to', 0))
                )
                temp_record.save()

            # Upload and encrypt required files
            for file_name in request.FILES:
                file = request.FILES.get(file_name)
                encrypted_path = handle_uploaded_file(file, str(user_request.id))
                file_prefix = "<" + file_name + "&>"
                uploads += file_prefix + encrypted_path + ","

            user_request.uploads = uploads.rstrip(',')
            user_request.save()
        
            return JsonResponse({'status': True, 'message': 'Successfully created request!', 'id': user_request.id})
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)})
    return JsonResponse({'status': False, 'message': 'Invalid request method'})

def get_request(request, id): 
    try:
        request_obj = Request.objects.get(id=id)
        request_serializer = RequestSerializer(request_obj)
        return JsonResponse(request_serializer.data, safe=False)
    except Request.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)

import hashlib
from ..models import generate_key_from_user, encrypt_data, decrypt_data

def handle_uploaded_file(file, source, source2=""):
    try:
        # Define the path where you want to save the file
        static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source))

        if source2:
            static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source), str(source2))

        # Create the upload directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(static_dir, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Hash the file path
        hashed_path = hashlib.sha256(file_path.encode()).hexdigest()
        
        # Encrypt the hashed path
        key = generate_key_from_user(source)
        encrypted_path = encrypt_data(hashed_path, key)
        
        return encrypted_path
    except Exception as e:
        raise Exception(f"Error handling file upload: {str(e)}")

def get_document_description(request, doc_code):
    try:
        document = Requirement.objects.get(code=doc_code)
        return JsonResponse({'description': document.description})
    except Requirement.DoesNotExist:
        return JsonResponse({'description': 'Document not found'}, status=404)

from django.contrib.auth import login

def display_payment(request, id):
    if request.method == "POST":
        user_request = get_if_exists(User_Request, id=id)

        if user_request:
            try:
                # Upload and encrypt payment file path
                for file_name in request.FILES:
                    file = request.FILES.get(file_name)
                    encrypted_path = handle_uploaded_file(file, str(user_request.id), 'uploaded_payment')
                    user_request.uploaded_payment = encrypted_path
                    user_request.status = "Waiting"
                    user_request.save()
                
                # If user is not authenticated, log them in
                if not request.user.is_authenticated:
                    # Get the user from the request
                    user = user_request.user
                    
                    # Authenticate the user (without password check since we already verified ownership)
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                
                return JsonResponse({
                    "status": True, 
                    "message": "Payment successful! Redirecting to your requests...",
                    "redirect": "/request/user/"
                })
            except Exception as e:
                return JsonResponse({"status": False, "message": f"Error processing payment: {str(e)}"})

        return JsonResponse({"status": False, "message": "Invalid payment detected. Please contact your administrator."})
    elif request.method == "GET":
        # Get the user request first
        requested_document = get_if_exists(User_Request, id=id)
        
        if not requested_document:
            return HttpResponse("Request not found. Please contact your administrator.")
            
        # Check if user is authenticated
        if request.user.is_authenticated:
            user = request.user
            # Verify this user owns the request
            if requested_document.user.id != user.id:
                return HttpResponse("Unauthorized access. This request belongs to another user.")
        else:
            # For unauthenticated users, check if they have a temp_user_email
            user_email = request.session.get('temp_user_email')
            if not user_email:
                return HttpResponse("Session expired. Please return to the main page and try again.")
                
            try:
                user = User.objects.get(email=user_email)
                # Verify this user owns the request
                if requested_document.user.id != user.id:
                    return HttpResponse("Unauthorized access. This request belongs to another user.")
            except User.DoesNotExist:
                return HttpResponse("User not found. Please register or login first.")

        # If we get here, the user is authorized to view this payment page
        return render(request, "payment.html", {"user": user, "requested_document": requested_document})

def display_user_requests(request):
    try:
        # Check if user is authenticated before querying
        if not request.user.is_authenticated:
            # Redirect to login page or show a message
            return render(request, 'user/request/view-user-request.html', {
                'user_requests': [],
                'message': 'Please log in to view your requests'
            })
        
        # Now we know we have an authenticated user with a valid ID
        user_requests = User_Request.objects.filter(user=request.user)
        
        for user_request in user_requests:
            # Decrypt requested file path if exists
            if user_request.requested:
                key = generate_key_from_user(str(user_request.id))
                decrypted_hash = decrypt_data(user_request.requested, key)
                base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(user_request.id), 'approved')
                
                if os.path.exists(base_path):
                    for filename in os.listdir(base_path):
                        file_path = os.path.join(base_path, filename)
                        current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                        if current_hash == decrypted_hash:
                            user_request.requested = file_path
                            break

            # Set payment status if needed
            if not user_request.uploaded_payment:
                user_request.payment_status = "Pending payment"
                user_request.save()

        return render(request, 'user/request/view-user-request.html', {'user_requests': user_requests})
    except Exception as e:
        # Add more detailed error information
        import traceback
        error_details = traceback.format_exc()
        print(error_details)  # Log the full traceback
        return HttpResponse(f"Error displaying user requests: {str(e)}")

import qrcode
from io import BytesIO
import base64

def generate_qr(request, id):
    try:
        user_request = User_Request.objects.get(id=id)
        if request.user != user_request.user:
            return HttpResponse("Unauthorized access", status=403)
            
        verification_url = request.build_absolute_uri(f'/verify-document/{id}/')
        document_name = user_request.request.document.description
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()
        
        return render(request, 'user/request/qr-code.html', {
            'qr_code': qr_image,
            'document_name': document_name
        })
    except User_Request.DoesNotExist:
        return HttpResponse("Request not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating QR code: {str(e)}")

def verify_document(request, document_id):
    try:
        user_request = User_Request.objects.get(id=document_id)
        
        context = {
            'document_name': user_request.request.document.description,
            'verification_date': user_request.updated_at,
            'student_number': user_request.user.student_number,
            'system_name': 'Academic Request System (ARS)'
        }
        
        return render(request, 'user/request/verify-document.html', context)
    except User_Request.DoesNotExist:
        return HttpResponse("Invalid document verification code", status=404)
