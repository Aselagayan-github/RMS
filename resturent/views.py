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
import base64
from io import BytesIO
from PIL import Image

# Set up logger
logger = logging.getLogger(__name__)

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')
db = client['resturent']
users_collection = db['users']
order_collection = db['order_table']
bookings_collection = db['bookings']
menu_items_collection = db['menu_items']  # Added for menu items

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

# Additional utility functions for orders

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

# ========== BOOKING MANAGEMENT API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET", "POST"])
def bookings_api(request):
    """
    GET: Retrieve all bookings
    POST: Create a new booking
    """
    if request.method == 'GET':
        return get_all_bookings(request)
    elif request.method == 'POST':
        return create_booking(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def booking_detail_api(request, booking_id):
    """
    GET: Retrieve a specific booking
    PUT: Update a specific booking
    DELETE: Delete a specific booking
    """
    if request.method == 'GET':
        return get_booking(request, booking_id)
    elif request.method == 'PUT':
        return update_booking(request, booking_id)
    elif request.method == 'DELETE':
        return delete_booking(request, booking_id)

def get_all_bookings(request):
    """Retrieve all bookings from MongoDB"""
    try:
        # Get query parameters for filtering and pagination
        status = request.GET.get('status')
        customer_name = request.GET.get('customer_name')
        date = request.GET.get('date')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        
        # Build query
        query = {}
        if status:
            query['status'] = status
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        if date:
            query['date'] = date
        
        # Retrieve bookings with sorting (newest first)
        bookings_cursor = bookings_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        bookings = []
        
        for booking in bookings_cursor:
            # Convert ObjectId to string for JSON serialization
            booking['_id'] = str(booking['_id'])
            
            # Ensure created_at exists
            if 'created_at' not in booking:
                booking['created_at'] = datetime.now().isoformat()
            
            bookings.append(booking)
        
        return JsonResponse(bookings, safe=False, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving bookings: {e}")
        return JsonResponse({'error': 'Failed to retrieve bookings', 'message': str(e)}, status=500)

def create_booking(request):
    """Create a new booking"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer_name', 'phone', 'date', 'time', 'guests', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate guests is a positive integer
        try:
            guests = int(data['guests'])
            if guests < 1:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Guests must be a positive integer'}, status=400)
        
        # Validate status
        valid_statuses = ['Confirmed', 'Pending', 'Cancelled']
        if data['status'] not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        
        # Add timestamps
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        # Insert booking into MongoDB
        result = bookings_collection.insert_one(data)
        
        # Return the created booking with ID
        data['_id'] = str(result.inserted_id)
        
        logger.info(f"Booking created successfully: {result.inserted_id}")
        return JsonResponse({
            'message': 'Booking created successfully',
            'booking_id': str(result.inserted_id),
            'booking': data
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return JsonResponse({'error': 'Failed to create booking', 'message': str(e)}, status=500)

def get_booking(request, booking_id):
    """Retrieve a specific booking by ID"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
        
        # Find the booking
        booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Convert ObjectId to string for JSON serialization
        booking['_id'] = str(booking['_id'])
        
        return JsonResponse(booking, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving booking {booking_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve booking', 'message': str(e)}, status=500)

def update_booking(request, booking_id):
    """Update a specific booking"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
        
        data = json.loads(request.body)
        
        # Add updated timestamp
        data['updated_at'] = datetime.now().isoformat()
        
        # Validate if status is being updated
        if 'status' in data:
            valid_statuses = ['Confirmed', 'Pending', 'Cancelled']
            if data['status'] not in valid_statuses:
                return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        
        # Validate guests if being updated
        if 'guests' in data:
            try:
                guests = int(data['guests'])
                if guests < 1:
                    raise ValueError
            except ValueError:
                return JsonResponse({'error': 'Guests must be a positive integer'}, status=400)
        
        # Update the booking
        result = bookings_collection.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Retrieve and return updated booking
        updated_booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
        updated_booking['_id'] = str(updated_booking['_id'])
        
        logger.info(f"Booking updated successfully: {booking_id}")
        return JsonResponse({
            'message': 'Booking updated successfully',
            'booking': updated_booking
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating booking {booking_id}: {e}")
        return JsonResponse({'error': 'Failed to update booking', 'message': str(e)}, status=500)

def delete_booking(request, booking_id):
    """Delete a specific booking"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
        
        # Delete the booking
        result = bookings_collection.delete_one({'_id': ObjectId(booking_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        logger.info(f"Booking deleted successfully: {booking_id}")
        return JsonResponse({'message': 'Booking deleted successfully'}, status=200)
    
    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {e}")
        return JsonResponse({'error': 'Failed to delete booking', 'message': str(e)}, status=500)

# ========== MENU MANAGEMENT API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET", "POST"])
def menu_items_api(request):
    """
    GET: Retrieve all menu items
    POST: Create a new menu item
    """
    if request.method == 'GET':
        return get_all_menu_items(request)
    elif request.method == 'POST':
        return create_menu_item(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def menu_item_detail_api(request, item_id):
    """
    GET: Retrieve a specific menu item
    PUT: Update a specific menu item
    DELETE: Delete a specific menu item
    """
    if request.method == 'GET':
        return get_menu_item(request, item_id)
    elif request.method == 'PUT':
        return update_menu_item(request, item_id)
    elif request.method == 'DELETE':
        return delete_menu_item(request, item_id)

def get_all_menu_items(request):
    """Retrieve all menu items from MongoDB"""
    try:
        # Get query parameters for filtering and pagination
        category = request.GET.get('category')
        availability = request.GET.get('availability')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        
        # Build query
        query = {}
        if category:
            query['category'] = category
        if availability:
            query['availability'] = availability
        
        # Retrieve menu items with sorting (newest first)
        items_cursor = menu_items_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        items = []
        
        for item in items_cursor:
            # Convert ObjectId to string for JSON serialization
            item['_id'] = str(item['_id'])
            # Ensure created_at exists
            if 'created_at' not in item:
                item['created_at'] = datetime.now().isoformat()
            items.append(item)
        
        return JsonResponse(items, safe=False, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving menu items: {e}")
        return JsonResponse({'error': 'Failed to retrieve menu items', 'message': str(e)}, status=500)

def create_menu_item(request):
    """Create a new menu item"""
    try:
        # Check if the request is multipart (contains file)
        if 'multipart/form-data' in request.content_type.lower():
            data = json.loads(request.POST.get('data', '{}'))
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            image_file = None

        # Validate required fields
        required_fields = ['name', 'category', 'price', 'availability']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate price
        try:
            price = float(data['price'])
            if price < 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Price must be a non-negative number'}, status=400)
        
        # Validate category
        valid_categories = ['Main Course', 'Appetizers', 'Desserts', 'Beverages']
        if data['category'] not in valid_categories:
            return JsonResponse({'error': f'Invalid category. Must be one of: {valid_categories}'}, status=400)
        
        # Validate availability
        valid_availabilities = ['Available', 'Unavailable']
        if data['availability'] not in valid_availabilities:
            return JsonResponse({'error': f'Invalid availability. Must be one of: {valid_availabilities}'}, status=400)
        
        # Handle image upload
        image_url = ''
        if image_file:
            try:
                # Validate image
                img = Image.open(image_file)
                img.verify()  # Verify image integrity
                img = Image.open(image_file)  # Reopen after verify
                img.thumbnail((200, 200))  # Resize to 200x200
                buffered = BytesIO()
                img.save(buffered, format=img.format or 'JPEG')
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                image_url = f"data:image/{img.format.lower()};base64,{image_data}"
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return JsonResponse({'error': 'Invalid image file'}, status=400)
        else:
            # Use placeholder image if none provided
            image_url = 'https://placehold.co/200x200/cccccc/969696?text=Image'

        # Prepare menu item data
        menu_item = {
            'name': data['name'],
            'category': data['category'],
            'price': float(data['price']),
            'availability': data['availability'],
            'description': data.get('description', ''),
            'image': image_url,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Insert menu item into MongoDB
        result = menu_items_collection.insert_one(menu_item)
        
        # Return the created menu item with ID
        menu_item['_id'] = str(result.inserted_id)
        
        logger.info(f"Menu item created successfully: {result.inserted_id}")
        return JsonResponse({
            'message': 'Menu item created successfully',
            'item_id': str(result.inserted_id),
            'item': menu_item
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating menu item: {e}")
        return JsonResponse({'error': 'Failed to create menu item', 'message': str(e)}, status=500)

def get_menu_item(request, item_id):
    """Retrieve a specific menu item by ID"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        
        # Find the menu item
        item = menu_items_collection.find_one({'_id': ObjectId(item_id)})
        
        if not item:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        
        # Convert ObjectId to string for JSON serialization
        item['_id'] = str(item['_id'])
        
        return JsonResponse(item, status=200)
    
    except Exception as e:
        logger.error(f"Error retrieving menu item {item_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve menu item', 'message': str(e)}, status=500)

def update_menu_item(request, item_id):
    """Update a specific menu item"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        
        # Check if the request is multipart (contains file)
        if 'multipart/form-data' in request.content_type.lower():
            data = json.loads(request.POST.get('data', '{}'))
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            image_file = None

        # Add updated timestamp
        data['updated_at'] = datetime.now().isoformat()
        
        # Validate if price is being updated
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    raise ValueError
            except ValueError:
                return JsonResponse({'error': 'Price must be a non-negative number'}, status=400)
        
        # Validate if category is being updated
        if 'category' in data:
            valid_categories = ['Main Course', 'Appetizers', 'Desserts', 'Beverages']
            if data['category'] not in valid_categories:
                return JsonResponse({'error': f'Invalid category. Must be one of: {valid_categories}'}, status=400)
        
        # Validate if availability is being updated
        if 'availability' in data:
            valid_availabilities = ['Available', 'Unavailable']
            if data['availability'] not in valid_availabilities:
                return JsonResponse({'error': f'Invalid availability. Must be one of: {valid_availabilities}'}, status=400)
        
        # Handle image upload if provided
        if image_file:
            try:
                img = Image.open(image_file)
                img.verify()  # Verify image integrity
                img = Image.open(image_file)  # Reopen after verify
                img.thumbnail((200, 200))  # Resize to 200x200
                buffered = BytesIO()
                img.save(buffered, format=img.format or 'JPEG')
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                data['image'] = f"data:image/{img.format.lower()};base64,{image_data}"
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return JsonResponse({'error': 'Invalid image file'}, status=400)
        
        # Update the menu item
        result = menu_items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        
        # Retrieve and return updated menu item
        updated_item = menu_items_collection.find_one({'_id': ObjectId(item_id)})
        updated_item['_id'] = str(updated_item['_id'])
        
        logger.info(f"Menu item updated successfully: {item_id}")
        return JsonResponse({
            'message': 'Menu item updated successfully',
            'item': updated_item
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating menu item {item_id}: {e}")
        return JsonResponse({'error': 'Failed to update menu item', 'message': str(e)}, status=500)

def delete_menu_item(request, item_id):
    """Delete a specific menu item"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        
        # Delete the menu item
        result = menu_items_collection.delete_one({'_id': ObjectId(item_id)})
        
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        
        logger.info(f"Menu item deleted successfully: {item_id}")
        return JsonResponse({'message': 'Menu item deleted successfully'}, status=200)
    
    except Exception as e:
        logger.error(f"Error deleting menu item {item_id}: {e}")
        return JsonResponse({'error': 'Failed to delete menu item', 'message': str(e)}, status=500)