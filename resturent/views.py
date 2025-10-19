from django.shortcuts import render, redirect
from django.contrib import messages
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson.objectid import ObjectId
from django.http import JsonResponse

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)


# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')
db = client['resturent']
users_collection = db['users']
order_collection = db['order_table']

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

def usermanage_view(request):
    return render(request, 'usermanagement.html')

def register(request):
    if request.method == 'POST':
        # Get form data
        idno = request.POST['idno']
        name = request.POST['name']
        address = request.POST['Address']
        contactno = request.POST['Contactno']
        gmail = request.POST['gmail']
        usertype = request.POST['Usertype']
        password = request.POST['password']

        if not all([idno, name, address, contactno, gmail, usertype, password]):
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
        logger.error(f"Error sending email: {e}")

def order_management_view(request):
    """Render the order management page"""
    return render(request, 'order_management.html')

# ========== ORDER MANAGEMENT API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET", "POST"])
def orders_api(request):
    """
    GET: Retrieve all orders
    POST: Create a new order
    """
    if request.method == 'GET':
        return get_all_orders(request)
    elif request.method == 'POST':
        return create_order(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def order_detail_api(request, order_id):
    """
    GET: Retrieve a specific order
    PUT: Update a specific order
    DELETE: Delete a specific order
    """
    if request.method == 'GET':
        return get_order(request, order_id)
    elif request.method == 'PUT':
        return update_order(request, order_id)
    elif request.method == 'DELETE':
        return delete_order(request, order_id)

def get_all_orders(request):
    """Retrieve all orders from MongoDB"""
    try:
        # Get query parameters for filtering and pagination
        status = request.GET.get('status')
        order_type = request.GET.get('order_type')
        customer_name = request.GET.get('customer_name')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        
        # Build query
        query = {}
        if status:
            query['status'] = status
        if order_type:
            query['order_type'] = order_type
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        
        # Retrieve orders with sorting (newest first)
        orders_cursor = order_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        orders = []
        
        for order in orders_cursor:
            # Convert ObjectId to string for JSON serialization
            order['_id'] = str(order['_id'])
            
            # Ensure created_at exists
            if 'created_at' not in order:
                order['created_at'] = datetime.now().isoformat()
            
            orders.append(order)
        
        return JsonResponse(orders, safe=False, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving orders: {e}")
        return JsonResponse({'error': 'Failed to retrieve orders', 'message': str(e)}, status=500)

def create_order(request):
    """Create a new order"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer_name', 'order_type', 'items']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate items structure (allow empty for now)
        if not isinstance(data['items'], list):
            return JsonResponse({'error': 'Items must be a list'}, status=400)
        
        for item in data['items']:
            required_item_fields = ['id', 'name', 'price', 'quantity']
            for field in required_item_fields:
                if field not in item:
                    return JsonResponse({'error': f'Missing required item field: {field}'}, status=400)
        
        # Calculate totals if not provided
        if 'subtotal' not in data or 'tax' not in data or 'total' not in data:
            subtotal = sum(float(item['price']) * int(item['quantity']) for item in data['items']) if data['items'] else 0.00
            tax = subtotal * 0.085
            total = subtotal + tax
            
            data['subtotal'] = f"{subtotal:.2f}"
            data['tax'] = f"{tax:.2f}"
            data['total'] = f"{total:.2f}"
        
        # Add timestamps and default status
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        if 'status' not in data:
            data['status'] = 'Pending'
        
        # Insert order into MongoDB
        result = order_collection.insert_one(data)
        
        # Return the created order with ID
        data['_id'] = str(result.inserted_id)
        
        logger.info(f"Order created successfully: {result.inserted_id}")
        return JsonResponse({
            'message': 'Order created successfully',
            'order_id': str(result.inserted_id),
            'order': data
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return JsonResponse({'error': 'Failed to create order', 'message': str(e)}, status=500)

def get_order(request, order_id):
    """Retrieve a specific order by ID"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        
        # Find the order
        order = order_collection.find_one({'_id': ObjectId(order_id)})
        
        if not order:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        # Convert ObjectId to string for JSON serialization
        order['_id'] = str(order['_id'])
        
        return JsonResponse(order, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve order', 'message': str(e)}, status=500)

def update_order(request, order_id):
    """Update a specific order"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        
        data = json.loads(request.body)
        
        # Add updated timestamp
        data['updated_at'] = datetime.now().isoformat()
        
        # If items are being updated, recalculate totals
        if 'items' in data and data['items']:
            subtotal = sum(float(item['price']) * int(item['quantity']) for item in data['items']) if data['items'] else 0.00
            tax = subtotal * 0.085
            total = subtotal + tax
            
            data['subtotal'] = f"{subtotal:.2f}"
            data['tax'] = f"{tax:.2f}"
            data['total'] = f"{total:.2f}"
        
        # Update the order
        result = order_collection.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        # Retrieve and return updated order
        updated_order = order_collection.find_one({'_id': ObjectId(order_id)})
        updated_order['_id'] = str(updated_order['_id'])
        
        logger.info(f"Order updated successfully: {order_id}")
        return JsonResponse({
            'message': 'Order updated successfully',
            'order': updated_order
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {e}")
        return JsonResponse({'error': 'Failed to update order', 'message': str(e)}, status=500)

def delete_order(request, order_id):
    """Delete a specific order"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        
        # Delete the order
        result = order_collection.delete_one({'_id': ObjectId(order_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        logger.info(f"Order deleted successfully: {order_id}")
        return JsonResponse({'message': 'Order deleted successfully'}, status=200)
    
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        return JsonResponse({'error': 'Failed to delete order', 'message': str(e)}, status=500)

# Additional utility functions

def get_order_statistics(request):
    """Get order statistics for dashboard"""
    try:
        # Total orders
        total_orders = order_collection.count_documents({})
        
        # Orders by status
        status_pipeline = [
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]
        status_stats = list(order_collection.aggregate(status_pipeline))
        
        # Revenue calculation
        revenue_pipeline = [
            {'$match': {'status': {'$in': ['Completed', 'Ready']}}},
            {'$group': {'_id': None, 'total_revenue': {'$sum': {'$toDouble': '$total'}}}}
        ]
        revenue_result = list(order_collection.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
        
        # Today's orders
        today = datetime.now().strftime('%Y-%m-%d')
        today_orders = order_collection.count_documents({
            'created_at': {'$regex': f'^{today}'}
        })
        
        # Popular items
        popular_items_pipeline = [
            {'$unwind': '$items'},
            {'$group': {
                '_id': '$items.name',
                'total_quantity': {'$sum': '$items.quantity'},
                'total_revenue': {'$sum': {'$multiply': ['$items.quantity', {'$toDouble': '$items.price'}]}}
            }},
            {'$sort': {'total_quantity': -1}},
            {'$limit': 5}
        ]
        popular_items = list(order_collection.aggregate(popular_items_pipeline))
        
        statistics = {
            'total_orders': total_orders,
            'status_distribution': {item['_id']: item['count'] for item in status_stats},
            'total_revenue': round(total_revenue, 2),
            'today_orders': today_orders,
            'popular_items': popular_items
        }
        
        return JsonResponse(statistics, status=200)
    
    except Exception as e:
        logger.error(f"Error getting order statistics: {e}")
        return JsonResponse({'error': 'Failed to get statistics', 'message': str(e)}, status=500)

# Save new order
def order_processing_view(request):
    if request.method == 'GET':
        # Fetch all orders from MongoDB
        orders = list(order_collection.find())
        for order in orders:
            order['_id'] = str(order['_id'])  # Convert ObjectId to string for frontend
        return render(request, 'order_processing.html', {'orders': orders})


@csrf_exempt
def add_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_data = {
            'customer': data.get('customer'),
            'time': data.get('time'),
            'status': data.get('status')
        }
        result = order_collection.insert_one(order_data)
        return JsonResponse({'success': True, 'order_id': str(result.inserted_id)})


@csrf_exempt
def delete_order(request, order_id):
    if request.method == 'POST':
        order_collection.delete_one({'_id': ObjectId(order_id)})
        return JsonResponse({'success': True})



@csrf_exempt
def update_order_status(request, order_id):
    """Update only the status of an order"""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if not new_status:
            return JsonResponse({'error': 'Status is required'}, status=400)
        
        valid_statuses = ['Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        
        result = order_collection.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {
                'status': new_status,
                'updated_at': datetime.now().isoformat()
            }}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        return JsonResponse({'message': f'Order status updated to {new_status}'}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        return JsonResponse({'error': 'Failed to update order status', 'message': str(e)}, status=500)