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
    return render(request, 'login.html')

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
    body = f"Hello {user_name},\n\nYour registration was successful! Welcome to our system."

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
