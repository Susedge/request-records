from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from ..models import Document
from ..models import Request
from ..models import Requirement
from ..models import User_Request
from ..serializers import RequestSerializer
from django.conf import settings
import os

def index(request):
    if request.method == "POST":
        post_document = request.POST.get("documents")
        post_files_required = request.POST.get("requirements")
        post_description = request.POST.get("description")
        post_price = request.POST.get("price")

        document = Document.objects.get(code = post_document)
        created_request = Request.objects.create(document=document, price=post_price, files_required=post_files_required, description=post_description)
        
        if created_request:
            return JsonResponse({"status": True, "message": "Request Created"})
        else:
            return JsonResponse({"status": False, "message": "Request not created. Please try again."})
    else:
        documents = Document.objects.all()
        requirements = Requirement.objects.all()
        return render(request, 'admin/request/index.html', {'documents': documents, 'requirements': requirements})

def display_user_requests(request):    
    user_requests = User_Request.objects.all()
    return render(request, 'admin/request/user-request.html', {'user_requests': user_requests })

def display_user_request(request, id):
    if request.method == "POST":
        new_status = request.POST.get('new_status')
        requested_file = request.FILES.get('requested_file')
        # payment_status = request.POST.get("payment_status")
        processing_time = request.POST.get("processing_time")
        pickup_schedule = request.POST.get("pickupSchedule")
        date_release = request.POST.get("dateRelease")
        remarks = request.POST.get("remarks")
        
        user_request = User_Request.objects.get(id=id)

        if requested_file is not None:
            # This will now return encrypted path
            encrypted_file_path = handle_uploaded_file(id, requested_file)
            user_request.requested = encrypted_file_path

        # user_request.payment_status = payment_status
        user_request.status = new_status
        user_request.remarks = remarks
        
        # Handle schedule and release date
        if pickup_schedule:
            from django.utils.dateparse import parse_datetime
            user_request.schedule = parse_datetime(pickup_schedule)
        
        if date_release:
            from django.utils.dateparse import parse_datetime
            user_request.date_release = parse_datetime(date_release)

        if processing_time:
            user_request.processing_time = processing_time
        elif processing_time:
            # Set a dynamic attribute for the calculate_date_release method
            user_request.processing_time = processing_time
            user_request.date_release = user_request.calculate_date_release()
        
        user_request.save()

        return JsonResponse({'status': True, 'message': 'Request status updated successfully.', 'request_status': user_request.status})    
    if request.method == "GET":
        try:
            user_request = User_Request.objects.get(id=id)
            uploads = []
        
            # Decrypt payment file path if exists
            if user_request.uploaded_payment:
                key = generate_key_from_user(id)
                decrypted_payment_hash = decrypt_data(user_request.uploaded_payment, key)
                payment_base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(id), 'uploaded_payment')
            
                if os.path.exists(payment_base_path):
                    for filename in os.listdir(payment_base_path):
                        file_path = os.path.join(payment_base_path, filename)
                        current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                        if current_hash == decrypted_payment_hash:
                            user_request.uploaded_payment = file_path
                            break
        
            if user_request.uploads:
                key = generate_key_from_user(id)
                upload_items = user_request.uploads.split(',')
                for user_request_upload in upload_items:
                    if user_request_upload.strip():
                        upload = user_request_upload.replace("<", "").replace(">", "").split('&')
                        # First decrypt the encrypted hash
                        decrypted_hash = decrypt_data(upload[1], key)
                    
                        # Reconstruct original file path
                        base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(id))
                    
                        # Check if base path exists
                        if os.path.exists(base_path):
                            for filename in os.listdir(base_path):
                                file_path = os.path.join(base_path, filename)
                                current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                                if current_hash == decrypted_hash:
                                    uploads.append({
                                        'code': getCodeDescription(Requirement, upload[0]),
                                        'path': file_path
                                    })
                                    break

            return render(request, 'admin/request/view-user-request.html', {
                'user_request': user_request,
                'uploads': uploads,
            })
        except User_Request.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'User request not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': False, 'message': f'Error: {str(e)}'}, status=500)   
                             
def getCodeDescription(model, key):
    try:
        model_instance = model.objects.get(code=key)
        return model_instance.description
    except model.DoesNotExist:
        return f"Unknown requirement ({key})"

def delete_user_request(request, id):
    user_request = User_Request.objects.get(id = id)
    user_request.delete()
    return JsonResponse({'status' : True, 'message': "Deleted succesfully."})
    
def delete_request(request, id):
    request = Request.objects.get(id=id)
    deleted = request.delete()

    if deleted:
        return JsonResponse({'status': True, 'message': deleted})
    else:
        return JsonResponse({'False': True, 'message': 'Invalid row'})
    
def get_requests(request):
    requests = Request.objects.all()
    requests_json = RequestSerializer(requests, many=True).data  # Serialize the queryset
    return JsonResponse(requests_json, safe=False)

import hashlib
from ..models import generate_key_from_user, encrypt_data, decrypt_data

def handle_uploaded_file(source, file):
    # Define the path where you want to save the file
    static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source), 'approved')

    # Create the upload directory if it doesn't exist
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Save the file
    file_path = os.path.join(static_dir, file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # First hash the path
    hashed_path = hashlib.sha256(file_path.encode()).hexdigest()
    
    # Then encrypt the hashed path
    key = generate_key_from_user(source)
    encrypted_path = encrypt_data(hashed_path, key)
    
    return encrypted_path