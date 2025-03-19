from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
import os
import shutil

@login_required
def upload_qr_code(request):
    # Path to the static QR code
    static_qr_path = os.path.join(settings.STATICFILES_DIRS[0], 'assets', 'img', 'gcash.jpg')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        qr_image = request.FILES.get('qr_image')
        
        if qr_image:
            # Validate file size
            if qr_image.size > 5 * 1024 * 1024:  # 5MB limit
                messages.error(request, "File size exceeds 5MB limit")
                return redirect('upload_qr_code')
                
            # Validate file type
            if not qr_image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                messages.error(request, "Only JPG and PNG files are allowed")
                return redirect('upload_qr_code')
                
            # Make backup of existing QR code
            if os.path.exists(static_qr_path):
                backup_path = static_qr_path + '.backup'
                shutil.copy2(static_qr_path, backup_path)
            
            # Save the new QR code
            with open(static_qr_path, 'wb+') as destination:
                for chunk in qr_image.chunks():
                    destination.write(chunk)
            
            messages.success(request, f"QR code for {payment_method} uploaded successfully")
            return redirect('upload_qr_code')
    
    # For GET request
    current_qr = None
    if os.path.exists(static_qr_path):
        current_qr = settings.STATIC_URL + 'assets/img/gcash.jpg'
    
    return render(request, 'admin/qr_upload.html', {
        'current_qr': current_qr,
        'current_method': 'GCASH'  # Default value
    })