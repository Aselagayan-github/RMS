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
        idno = request.POST.get('idno')
        name = request.POST.get('name')
        address = request.POST.get('Address')
        contact_no = request.POST.get('Contactno')
        gmail = request.POST.get('gmail')
        user_type = request.POST.get('Usertype')
        table_type = request.POST.get('tabletype')
        type_ = request.POST.get('type')
        password = request.POST.get('password')

        if not all([idno, name, address, contact_no, gmail, user_type, table_type, type_, password]):
            messages.error(request, 'All fields are required. Please fill in all fields.')
            return render(request, 'register.html')

        # Save user data to MongoDB
        user_data = {
            'idno': idno,
            'name': name,
            'address': address,
            'contact_no': contact_no,
            'gmail': gmail,
            'user_type': user_type,
            'table_type': table_type,
            'type': type_,
            'password': password,
        }
        users_collection.insert_one(user_data)

        # Send confirmation email
        try:
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

                # Email content
                subject = "Registration Successful"
                body = f"Hello {name},\n\nThank you for registering!\n\nBest regards,\nTeam"
                msg = MIMEMultipart()
                msg['From'] = EMAIL_ADDRESS
                msg['To'] = gmail
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                smtp.sendmail(EMAIL_ADDRESS, gmail, msg.as_string())
        except Exception as e:
            print("Error sending email:", e)

        # Show success message and redirect to login page
        messages.success(request, 'Registration successful! A confirmation email has been sent.')
        return redirect('login')
    
    return render(request, 'register.html')
