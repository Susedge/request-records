function showToast(options) {
    let toast = Toastify({
        text: options.message,
        duration: 2000,
        newWindow: true,
        close: true,
        gravity: "top",
        position: "right",
        stopOnFocus: true,
        style: {
            background: options.color || "#007bff",
        },
    });

    toast.showToast();
}

$(document).ready(function() {
    // Events
    $('#btnCreate').click(function() {
        let selectedRequest = document.querySelector("#request")

        showToast({message: "Creating request form please wait..."})
        getRequest(selectedRequest.value, createRequestForm);
    });

    // Web services
    function getRequest(id, successCallBack, errorCallBack){
        $.ajax({
            type: 'GET',
            url: '/request/' + id + '/',
            success: function(response) {
                successCallBack(response);
            },
            error: function(xhr, errmsg, err) {
                console.log(errmsg);
            }
        });
    }
    
    function createRequestForm(response) {
        let data = response;
        let requestID = data.id;

        // Debug
        console.log(data);

        const container = document.getElementById("container");
        container.innerHTML = "";

        // Fill up the form
        const h2ForRequiredFiles = document.createElement("h5");
        h2ForRequiredFiles.innerHTML = data.document;
        h2ForRequiredFiles.classList.add("mb-3");

        const price = document.createElement("span");
        price.textContent = "₱" + data.price;
        price.classList.add("mx-2", "badge", "bg-primary");
        h2ForRequiredFiles.appendChild(price);
        container.appendChild(h2ForRequiredFiles);

        // Create textarea for description
        const descriptionTextarea = document.createElement("p");
        descriptionTextarea.id = "description";
        descriptionTextarea.name = "description";
        descriptionTextarea.textContent = data.description;
        container.appendChild(descriptionTextarea);

        // Purpose
        const lblPurpose = document.createElement("h5");
        lblPurpose.innerHTML = "Purpose:";
        container.appendChild(lblPurpose);

        // Purpose dropdown
        const drpPurpose = document.createElement("select");
        drpPurpose.classList.add("form-select"); 
        drpPurpose.setAttribute("id", "drpPurpose")
        drpPurpose.classList.add("mb-3") // Add margin left 3
        drpPurpose.name = "purpose";

        const purposes = data.purpose;
        purposes.forEach((purpose) => {
            const optPurpose = document.createElement("option");
            optPurpose.value = purpose.description;
            optPurpose.textContent = purpose.description;
            drpPurpose.appendChild(optPurpose);
        })

        // Add "Others" option
        const optOthers = document.createElement("option");
        optOthers.value = "Others";
        optOthers.textContent = "Others";
        drpPurpose.appendChild(optOthers);
        
        // Add event listener for when purpose changes
        drpPurpose.addEventListener("change", function() {
            // Remove existing custom purpose input if it exists
            const existingCustomInput = document.getElementById("customPurposeContainer");
            if (existingCustomInput) {
                existingCustomInput.remove();
            }
            
            // If "Others" is selected, show the custom input field
            if (this.value === "Others") {
                const customPurposeContainer = document.createElement("div");
                customPurposeContainer.id = "customPurposeContainer";
                customPurposeContainer.classList.add("mb-3");
                
                const customPurposeLabel = document.createElement("label");
                customPurposeLabel.textContent = "Please specify your purpose:";
                customPurposeLabel.classList.add("form-label");
                
                const customPurposeInput = document.createElement("input");
                customPurposeInput.type = "text";
                customPurposeInput.id = "customPurpose";
                customPurposeInput.classList.add("form-control");
                customPurposeInput.required = true;
                customPurposeInput.placeholder = "Enter your purpose here";
                
                customPurposeContainer.appendChild(customPurposeLabel);
                customPurposeContainer.appendChild(customPurposeInput);
                
                // Insert after the dropdown
                drpPurpose.parentNode.insertBefore(customPurposeContainer, drpPurpose.nextSibling);
            }
        });

        container.appendChild(drpPurpose);
    
        // // Number of copies
        // const lblCopies = document.createElement("h5");
        // lblCopies.innerHTML = "Number of Copies:";
        // container.appendChild(lblCopies);
    
        // // Create number input for copies
        // const copiesContainer = document.createElement("div");
        // copiesContainer.classList.add("mb-3");
    
        // const copiesInput = document.createElement("input");
        // copiesInput.setAttribute("type", "number");
        // copiesInput.setAttribute("id", "numCopies");
        // copiesInput.setAttribute("min", "1");
        // copiesInput.setAttribute("max", "10");
        // copiesInput.setAttribute("value", "1");
        // copiesInput.classList.add("form-control");
    
        // copiesContainer.appendChild(copiesInput);
        // container.appendChild(copiesContainer);

        // Create label
        const h2 = document.createElement("h5");
        h2.innerHTML = "Required Files:";
        container.appendChild(h2);

        // Create upload input for files_required
        const requiredFiles = (data.files_required).split(',');
        requiredFiles.forEach((requiredFile) => {
            let fileInputContainer = document.createElement("div");
            fileInputContainer.classList.add("mb-3");

            let fileLabel = document.createElement("label");
            fileLabel.setAttribute("for", requiredFile);

            // Fetch document description for the required file code
            getDocumentDescription(requiredFile, function(description) {
                fileLabel.textContent = description;
            });

            let fileInput = document.createElement("input");
            fileInput.setAttribute("type", "file");
            fileInput.setAttribute("id", requiredFile);
            fileInput.classList.add("form-control");
            fileInput.required = true;

            fileInputContainer.appendChild(fileLabel);
            fileInputContainer.appendChild(fileInput);
            container.appendChild(fileInputContainer);
        });

        // Create submit button
        const btnSubmitRequest = document.createElement("button");
        btnSubmitRequest.id = "btnSubmitRequest";
        btnSubmitRequest.textContent = "Submit Request";
        btnSubmitRequest.addEventListener("click", () => {
            submitRequest(requestID, data);
        })
        btnSubmitRequest.type = "button";
        btnSubmitRequest.classList.add("btn", "btn-primary"); // Add Bootstrap classes
        container.appendChild(btnSubmitRequest);
    }
});

function submitRequest(id, request){
    const files = document.querySelectorAll('input[type="file"]');

    if (!validateForm()) {
        showToast({ message: 'Form submission failed due to missing required files.', color: '#FF0000' });
        return; // Do not proceed with form submission
    }

    if (!validateFileSize(files)) {
        return;
    }

    var csrftoken = getCookie('csrftoken');

    // Create form data
    var formData = new FormData();

    formData.append("id", id);
    files.forEach((file, index) => {
        // Skip authorization_letter as we'll handle it separately
        if (file.id !== 'authorization_letter') {
            // Append each file to the FormData object
            formData.append(`${file.id}`, file.files[0]);
        }
    });

    // Add authorization letter if provided
    const authLetterInput = document.getElementById('authorization_letter');
    if (authLetterInput && authLetterInput.files.length > 0) {
        formData.append('authorization_letter', authLetterInput.files[0]);
    }

    // Add null check for drpPurpose
    const purposeElement = document.querySelector("#drpPurpose");
    if (purposeElement) {
        // Check if "Others" is selected and custom purpose input exists
        if (purposeElement.value === "Others") {
            const customPurposeInput = document.querySelector("#customPurpose");
            if (customPurposeInput && customPurposeInput.value.trim()) {
                formData.append('purpose', "Other: " + customPurposeInput.value.trim());
            } else {
                showToast({ message: 'Please specify your purpose.', color: '#FF0000' });
                return;
            }
        } else {
            formData.append('purpose', purposeElement.value);
        }
    } else {
        // Use a default value or get it from request object if available
        formData.append('purpose', request?.purpose?.[0]?.description || 'General Purpose');
        console.warn("Purpose dropdown not found in DOM, using fallback value");
    }
    
    // Get number_of_copies from the outer form instead of the dynamically created form
    const numberOfCopiesElement = document.querySelector("#number_of_copies");
    if (numberOfCopiesElement) {
        formData.append('number_of_copies', numberOfCopiesElement.value);
    } else {
        formData.append('number_of_copies', '1'); // Default to 1 if not found
    }
    
    // Create temp_user_info object if profile form exists
    if (document.getElementById('profile-form')) {
        const profileForm = document.getElementById('profile-form');
        // Create temp_user_info JSON object
        const temp_user_info = {
            first_name: profileForm.querySelector('#first-name').value,
            last_name: profileForm.querySelector('#last-name').value,
            middle_name: profileForm.querySelector('#middle-name').value || '',
            user_type: profileForm.querySelector('#user-type').value,
            contact_no: profileForm.querySelector('#contact-no').value,
            course: profileForm.querySelector('#course').value,
            entry_year_from: profileForm.querySelector('#entry-year-from').value,
            entry_year_to: profileForm.querySelector('#entry-year-to').value,
            timestamp: new Date().toISOString()
        };
        
        // Append as separate parameter
        formData.append('temp_user_info', JSON.stringify(temp_user_info));
        
        // Also send user_type separately for immediate update
        formData.append('user_type', profileForm.querySelector('#user-type').value);
    }

    // Send AJAX POST request
    $.ajax({
        type: 'POST',
        url: '/request/user/create/',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            showToast({
                'message': response.message,
                'duration': 3000
            });

            if (response.status) {
                setTimeout(function() {
                    let isNewTabOpened = openPaymentTab(formData, response.id);

                    if (isNewTabOpened){
                        // Disable page
                        document.body.classList.toggle('overlay');
                    }
                }, 4000);
            }
        },
        error: function(xhr, errmsg, err) {
            console.log(errmsg);
            showToast({
                message: 'An error occurred. Please try again.',
                color: '#FF0000'
            });
        }
    });
}

function validateFileSize(files) {
    const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    let isValid = true;
    
    files.forEach(file => {
        if (file.files[0] && file.files[0].size > MAX_FILE_SIZE) {
            showToast({
                message: `File ${file.files[0].name} exceeds 25MB limit`,
                color: '#FF0000'
            });
            isValid = false;
        }
    });
    
    // Check authorization letter size if provided
    const authLetterInput = document.getElementById('authorization_letter');
    if (authLetterInput && authLetterInput.files.length > 0 && authLetterInput.files[0].size > MAX_FILE_SIZE) {
        showToast({
            message: `Authorization letter exceeds 25MB limit`,
            color: '#FF0000'
        });
        isValid = false;
    }
    
    return isValid;
}

function openPaymentTab(formData, requestID){
    sessionStorage.clear();
    sessionStorage.setItem("data", formData);
    return openNewTab("/request/checkout/" + requestID, 800, 800);
}

function openNewTab(url, width, height){
    // Debug
    console.log("New tab opened: " + url);
    var leftPosition, topPosition;
    //Allow for borders.
    leftPosition = (window.screen.width / 2) - ((width / 2) + 10);

    //Allow for title and status bars.
    topPosition = (window.screen.height / 2) - ((height / 2) + 50);

    //Open the window.
    let openedWindow = window.open(url, "Window2",
    "status=no,height=" + height + ",width=" + width + ",resizable=yes,left="
    + leftPosition + ",top=" + topPosition + ",screenX=" + leftPosition + ",screenY="
    + topPosition + ",toolbar=no,menubar=no,scrollbars=no,location=no,directories=no");

    let intervalId = setInterval(function() {
        if (openedWindow.closed) {
            clearInterval(intervalId); // Clear the interval
            console.log("Back to the main page"); // Debug

            window.focus();
            document.body.classList.toggle('overlay');
            
            setTimeout(function() {
                window.location.href='/request/user/'
            }, 1000);
        }
    }, 500);

    return true;
}

function getDocumentDescription(docCode, callback) {
    $.ajax({
        type: 'GET',
        url: '/get-document-description/' + docCode + '/',
        success: function(response) {
            callback(response.description);
        },
        error: function(xhr, errmsg, err) {
            console.log(errmsg);
        }
    });
}

// Function to get CSRF cookie value
function getCookie(name) {
    var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
    return cookieValue;
}

function validateForm() {
    const fileInputs = document.querySelectorAll('input[type="file"][required]');
    let isValid = true;

    fileInputs.forEach(input => {
        if (!input.value) {
            isValid = false;
        }
    });

    // Validate custom purpose if "Others" is selected
    const purposeElement = document.querySelector("#drpPurpose");
    if (purposeElement && purposeElement.value === "Others") {
        const customPurposeInput = document.querySelector("#customPurpose");
        if (!customPurposeInput || !customPurposeInput.value.trim()) {
            isValid = false;
            if (customPurposeInput) {
                customPurposeInput.classList.add('is-invalid');
            }
        } else if (customPurposeInput) {
            customPurposeInput.classList.remove('is-invalid');
        }
    }

    // Also validate profile form if it exists
    if (document.getElementById('profile-form')) {
        const requiredFields = document.getElementById('profile-form').querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
    }

    return isValid;
}

function validateFileSize(files) {
    const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    let isValid = true;
    
    files.forEach(file => {
        if (file.files[0] && file.files[0].size > MAX_FILE_SIZE) {
            showToast({
                message: `File ${file.files[0].name} exceeds 25MB limit`,
                color: '#FF0000'
            });
            isValid = false;
        }
    });
    
    return isValid;
}
