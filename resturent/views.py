from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')
db = client['resturent']
users_collection = db['users']

# Email credentials
EMAIL_ADDRESS = 'aselagayan1010@gmail.com'
EMAIL_PASSWORD = 'ffyyreefwwtuelyb'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

def main_page(request):
    return render(request, 'main.html')

def menu(request):
    return render(request, 'menu.html')

def blog(request):
    return render(request, 'blog.html')

def contact(request):
    return render(request, 'contact.html')

def login(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        usertype = request.POST.get('Usertype')

        # Check if the fields are empty
        if not username or not password or usertype == 'Not Selected':
            messages.error(request, 'All fields are required.')
            return render(request, 'login.html')

        # Query MongoDB for the user with the given username and password
        user = users_collection.find_one({'name': username, 'password': password})

        if user:
            # If user exists and user type matches
            if user['usertype'] == 'Admin':
                return redirect('admindashboard')
            elif user['usertype'] == 'Customer':
                return redirect('customerdashboard')
            else:
                messages.error(request, 'Invalid user type.')
                return render(request, 'login.html')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')

def admin_view(request):
    return render(request, 'admindashboard.html')

def customer_view(request):
    return render(request, 'customerdashboard.html')

def register(request):
    if request.method == 'POST':
        # Get form data
        idno = request.POST['idno']
        name = request.POST['name']
        address = request.POST['Address']
        contactno = request.POST['Contactno']
        gmail = request.POST['gmail']
        usertype = request.POST['Usertype']
        type = request.POST['type']
        tabletype = request.POST['tabletype']
        password = request.POST['password']

        if not all([idno, name, address, contactno, gmail, usertype, type, tabletype, password]):
            messages.error(request, 'All fields are required. Please fill in all fields.')
            return render(request, 'register.html')

        # Save user data in MongoDB
        user_data = {
            'idno': idno,
            'name': name,
            'address': address,
            'contactno': contactno,
            'gmail': gmail,
            'usertype': usertype,
            'type': type,
            'tabletype': tabletype,
            'password': password
        }
        
        # Insert user data into MongoDB
        users_collection.insert_one(user_data)

        # Send confirmation email to the user
        send_email(gmail, name)

        # Show success message
        messages.success(request, "Registration successful! Check your email for confirmation.")

        # Redirect to login page
        return redirect('login')
    
    return render(request, 'register.html')

def send_email(to_email, user_name):
    # Create the email content
    subject = "Registration Successful"
    body = f"Hello {user_name},\n\nYour registration was successful! Welcome to our system. \n\nBest regards,\nTeam"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, to_email, text)
    except Exception as e:
        print(f"Error sending email: {e}")
