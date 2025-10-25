from django.shortcuts import render, redirect
from django.contrib import messages
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson.objectid import ObjectId
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import logging
import base64
from io import BytesIO
from PIL import Image
import os
import subprocess

# Set up logger
logger = logging.getLogger(__name__)

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')
db = client['resturent']
users_collection = db['users']
order_collection = db['order_table']
bookings_collection = db['bookings']
menu_items_collection = db['menu_items']
deliveries_collection = db['deliveries']
invoices_collection = db['invoices']  # New collection for invoices

# Email credentials
EMAIL_ADDRESS = 'aselagayan1010@gmail.com'
EMAIL_PASSWORD = 'ffyyreefwwtuelyb'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

# Existing views
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        usertype = request.POST.get('Usertype')
        if not username or not password or usertype == 'Not Selected':
            messages.error(request, 'All fields are required.')
            return render(request, 'login.html')
        user = users_collection.find_one({'name': username, 'password': password})
        if user:
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
        user_data = {
            'idno': idno,
            'name': name,
            'address': address,
            'contactno': contactno,
            'gmail': gmail,
            'usertype': usertype,
            'password': password
        }
        users_collection.insert_one(user_data)
        send_email(gmail, name)
        messages.success(request, "Registration successful! Check your email for confirmation.")
        return redirect('login')
    return render(request, 'register.html')

def send_email(to_email, user_name):
    subject = "Registration Successful"
    body = f"Hello {user_name},\n\nYour registration was successful! Welcome to our system. \n\nBest regards,\nTeam"
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, to_email, text)
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def order_management_view(request):
    return render(request, 'order_management.html')

# ========== ORDER MANAGEMENT API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET", "POST"])
def orders_api(request):
    if request.method == 'GET':
        return get_all_orders(request)
    elif request.method == 'POST':
        return create_order(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def order_detail_api(request, order_id):
    if request.method == 'GET':
        return get_order(request, order_id)
    elif request.method == 'PUT':
        return update_order(request, order_id)
    elif request.method == 'DELETE':
        return delete_order(request, order_id)

def get_all_orders(request):
    try:
        status = request.GET.get('status')
        order_type = request.GET.get('order_type')
        customer_name = request.GET.get('customer_name')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        query = {}
        if status:
            query['status'] = status
        if order_type:
            query['order_type'] = order_type
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        orders_cursor = order_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        orders = []
        for order in orders_cursor:
            order['_id'] = str(order['_id'])
            if 'created_at' not in order:
                order['created_at'] = datetime.now().isoformat()
            orders.append(order)
        return JsonResponse(orders, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error retrieving orders: {e}")
        return JsonResponse({'error': 'Failed to retrieve orders', 'message': str(e)}, status=500)

def create_order(request):
    try:
        data = json.loads(request.body)
        required_fields = ['customer_name', 'order_type', 'items']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        if not isinstance(data['items'], list):
            return JsonResponse({'error': 'Items must be a list'}, status=400)
        for item in data['items']:
            required_item_fields = ['id', 'name', 'price', 'quantity']
            for field in required_item_fields:
                if field not in item:
                    return JsonResponse({'error': f'Missing required item field: {field}'}, status=400)
        if 'subtotal' not in data or 'tax' not in data or 'total' not in data:
            subtotal = sum(float(item['price']) * int(item['quantity']) for item in data['items']) if data['items'] else 0.00
            tax = subtotal * 0.085
            total = subtotal + tax
            data['subtotal'] = f"{subtotal:.2f}"
            data['tax'] = f"{tax:.2f}"
            data['total'] = f"{total:.2f}"
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        if 'status' not in data:
            data['status'] = 'Pending'
        result = order_collection.insert_one(data)
        data['_id'] = str(result.inserted_id)
        # Create invoice on order creation
        create_invoice_from_order(data)
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
    try:
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        order = order_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return JsonResponse({'error': 'Order not found'}, status=404)
        order['_id'] = str(order['_id'])
        return JsonResponse(order, status=200)
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve order', 'message': str(e)}, status=500)

def update_order(request, order_id):
    try:
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        data = json.loads(request.body)
        data['updated_at'] = datetime.now().isoformat()
        if 'items' in data and data['items']:
            subtotal = sum(float(item['price']) * int(item['quantity']) for item in data['items']) if data['items'] else 0.00
            tax = subtotal * 0.085
            total = subtotal + tax
            data['subtotal'] = f"{subtotal:.2f}"
            data['tax'] = f"{tax:.2f}"
            data['total'] = f"{total:.2f}"
        result = order_collection.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': data}
        )
        if result.matched_count == 0:
            return JsonResponse({'error': 'Order not found'}, status=404)
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
    try:
        if not ObjectId.is_valid(order_id):
            return JsonResponse({'error': 'Invalid order ID format'}, status=400)
        result = order_collection.delete_one({'_id': ObjectId(order_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Order not found'}, status=404)
        logger.info(f"Order deleted successfully: {order_id}")
        return JsonResponse({'message': 'Order deleted successfully'}, status=200)
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        return JsonResponse({'error': 'Failed to delete order', 'message': str(e)}, status=500)

def get_order_statistics(request):
    try:
        total_orders = order_collection.count_documents({})
        status_pipeline = [
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]
        status_stats = list(order_collection.aggregate(status_pipeline))
        revenue_pipeline = [
            {'$match': {'status': {'$in': ['Completed', 'Ready']}}},
            {'$group': {'_id': None, 'total_revenue': {'$sum': {'$toDouble': '$total'}}}}
        ]
        revenue_result = list(order_collection.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
        today = datetime.now().strftime('%Y-%m-%d')
        today_orders = order_collection.count_documents({
            'created_at': {'$regex': f'^{today}'}
        })
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
    if request.method == 'GET':
        return get_all_bookings(request)
    elif request.method == 'POST':
        return create_booking(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def booking_detail_api(request, booking_id):
    if request.method == 'GET':
        return get_booking(request, booking_id)
    elif request.method == 'PUT':
        return update_booking(request, booking_id)
    elif request.method == 'DELETE':
        return delete_booking(request, booking_id)

def get_all_bookings(request):
    try:
        status = request.GET.get('status')
        customer_name = request.GET.get('customer_name')
        date = request.GET.get('date')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        query = {}
        if status:
            query['status'] = status
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        if date:
            query['date'] = date
        bookings_cursor = bookings_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        bookings = []
        for booking in bookings_cursor:
            booking['_id'] = str(booking['_id'])
            if 'created_at' not in booking:
                booking['created_at'] = datetime.now().isoformat()
            bookings.append(booking)
        return JsonResponse(bookings, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error retrieving bookings: {e}")
        return JsonResponse({'error': 'Failed to retrieve bookings', 'message': str(e)}, status=500)

def create_booking(request):
    try:
        data = json.loads(request.body)
        required_fields = ['customer_name', 'phone', 'date', 'time', 'guests', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        try:
            guests = int(data['guests'])
            if guests < 1:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Guests must be a positive integer'}, status=400)
        valid_statuses = ['Confirmed', 'Pending', 'Cancelled']
        if data['status'] not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        result = bookings_collection.insert_one(data)
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
    try:
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
        booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        booking['_id'] = str(booking['_id'])
        return JsonResponse(booking, status=200)
    except Exception as e:
        logger.error(f"Error retrieving booking {booking_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve booking', 'message': str(e)}, status=500)

def update_booking(request, booking_id):
    try:
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
        data = json.loads(request.body)
        data['updated_at'] = datetime.now().isoformat()
        if 'status' in data:
            valid_statuses = ['Confirmed', 'Pending', 'Cancelled']
            if data['status'] not in valid_statuses:
                return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        if 'guests' in data:
            try:
                guests = int(data['guests'])
                if guests < 1:
                    raise ValueError
            except ValueError:
                return JsonResponse({'error': 'Guests must be a positive integer'}, status=400)
        result = bookings_collection.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': data}
        )
        if result.matched_count == 0:
            return JsonResponse({'error': 'Booking not found'}, status=404)
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
    try:
        if not ObjectId.is_valid(booking_id):
            return JsonResponse({'error': 'Invalid booking ID format'}, status=400)
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
    if request.method == 'GET':
        return get_all_menu_items(request)
    elif request.method == 'POST':
        return create_menu_item(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def menu_item_detail_api(request, item_id):
    if request.method == 'GET':
        return get_menu_item(request, item_id)
    elif request.method == 'PUT':
        return update_menu_item(request, item_id)
    elif request.method == 'DELETE':
        return delete_menu_item(request, item_id)

def get_all_menu_items(request):
    try:
        category = request.GET.get('category')
        availability = request.GET.get('availability')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        query = {}
        if category:
            query['category'] = category
        if availability:
            query['availability'] = availability
        items_cursor = menu_items_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        items = []
        for item in items_cursor:
            item['_id'] = str(item['_id'])
            if 'created_at' not in item:
                item['created_at'] = datetime.now().isoformat()
            items.append(item)
        return JsonResponse(items, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error retrieving menu items: {e}")
        return JsonResponse({'error': 'Failed to retrieve menu items', 'message': str(e)}, status=500)

def create_menu_item(request):
    try:
        if 'multipart/form-data' in request.content_type.lower():
            data = json.loads(request.POST.get('data', '{}'))
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            image_file = None
        required_fields = ['name', 'category', 'price', 'availability']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        try:
            price = float(data['price'])
            if price < 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Price must be a non-negative number'}, status=400)
        valid_categories = ['Main Course', 'Appetizers', 'Desserts', 'Beverages']
        if data['category'] not in valid_categories:
            return JsonResponse({'error': f'Invalid category. Must be one of: {valid_categories}'}, status=400)
        valid_availabilities = ['Available', 'Unavailable']
        if data['availability'] not in valid_availabilities:
            return JsonResponse({'error': f'Invalid availability. Must be one of: {valid_availabilities}'}, status=400)
        image_url = ''
        if image_file:
            try:
                img = Image.open(image_file)
                img.verify()
                img = Image.open(image_file)
                img.thumbnail((200, 200))
                buffered = BytesIO()
                img_format = img.format or 'JPEG'
                img.save(buffered, format=img_format)
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                image_url = f"data:image/{img_format.lower()};base64,{image_data}"
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return JsonResponse({'error': 'Invalid image file'}, status=400)
        else:
            image_url = 'https://placehold.co/200x200/cccccc/969696?text=Image'
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
        result = menu_items_collection.insert_one(menu_item)
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
    try:
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        item = menu_items_collection.find_one({'_id': ObjectId(item_id)})
        if not item:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        item['_id'] = str(item['_id'])
        return JsonResponse(item, status=200)
    except Exception as e:
        logger.error(f"Error retrieving menu item {item_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve menu item', 'message': str(e)}, status=500)

def update_menu_item(request, item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        if 'multipart/form-data' in request.content_type.lower():
            data = json.loads(request.POST.get('data', '{}'))
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            image_file = None
        data['updated_at'] = datetime.now().isoformat()
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    raise ValueError
            except ValueError:
                return JsonResponse({'error': 'Price must be a non-negative number'}, status=400)
        if 'category' in data:
            valid_categories = ['Main Course', 'Appetizers', 'Desserts', 'Beverages']
            if data['category'] not in valid_categories:
                return JsonResponse({'error': f'Invalid category. Must be one of: {valid_categories}'}, status=400)
        if 'availability' in data:
            valid_availabilities = ['Available', 'Unavailable']
            if data['availability'] not in valid_availabilities:
                return JsonResponse({'error': f'Invalid availability. Must be one of: {valid_availabilities}'}, status=400)
        if image_file:
            try:
                img = Image.open(image_file)
                img.verify()
                img = Image.open(image_file)
                img.thumbnail((200, 200))
                buffered = BytesIO()
                img_format = img.format or 'JPEG'
                img.save(buffered, format=img_format)
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                data['image'] = f"data:image/{img_format.lower()};base64,{image_data}"
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return JsonResponse({'error': 'Invalid image file'}, status=400)
        result = menu_items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': data}
        )
        if result.matched_count == 0:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
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
    try:
        if not ObjectId.is_valid(item_id):
            return JsonResponse({'error': 'Invalid item ID format'}, status=400)
        result = menu_items_collection.delete_one({'_id': ObjectId(item_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        logger.info(f"Menu item deleted successfully: {item_id}")
        return JsonResponse({'message': 'Menu item deleted successfully'}, status=200)
    except Exception as e:
        logger.error(f"Error deleting menu item {item_id}: {e}")
        return JsonResponse({'error': 'Failed to delete menu item', 'message': str(e)}, status=500)

# ========== DELIVERY MANAGEMENT API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET", "POST"])
def deliveries_api(request):
    if request.method == 'GET':
        return get_all_deliveries(request)
    elif request.method == 'POST':
        return create_delivery(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def delivery_detail_api(request, delivery_id):
    if request.method == 'GET':
        return get_delivery(request, delivery_id)
    elif request.method == 'PUT':
        return update_delivery(request, delivery_id)
    elif request.method == 'DELETE':
        return delete_delivery(request, delivery_id)

def get_all_deliveries(request):
    try:
        status = request.GET.get('status')
        customer_name = request.GET.get('customer_name')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        query = {}
        if status:
            query['status'] = status
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        deliveries_cursor = deliveries_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        deliveries = []
        for delivery in deliveries_cursor:
            delivery['_id'] = str(delivery['_id'])
            if 'created_at' not in delivery:
                delivery['created_at'] = datetime.now().isoformat()
            deliveries.append(delivery)
        return JsonResponse(deliveries, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error retrieving deliveries: {e}")
        return JsonResponse({'error': 'Failed to retrieve deliveries', 'message': str(e)}, status=500)

def create_delivery(request):
    try:
        data = json.loads(request.body)
        required_fields = ['order_id', 'customer_name', 'address', 'driver', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        valid_statuses = ['Ready for Pickup', 'Out for Delivery', 'Delivered', 'Cancelled']
        if data['status'] not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        result = deliveries_collection.insert_one(data)
        data['_id'] = str(result.inserted_id)
        logger.info(f"Delivery created successfully: {result.inserted_id}")
        return JsonResponse({
            'message': 'Delivery created successfully',
            'delivery_id': str(result.inserted_id),
            'delivery': data
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating delivery: {e}")
        return JsonResponse({'error': 'Failed to create delivery', 'message': str(e)}, status=500)

def get_delivery(request, delivery_id):
    try:
        if not ObjectId.is_valid(delivery_id):
            return JsonResponse({'error': 'Invalid delivery ID format'}, status=400)
        delivery = deliveries_collection.find_one({'_id': ObjectId(delivery_id)})
        if not delivery:
            return JsonResponse({'error': 'Delivery not found'}, status=404)
        delivery['_id'] = str(delivery['_id'])
        return JsonResponse(delivery, status=200)
    except Exception as e:
        logger.error(f"Error retrieving delivery {delivery_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve delivery', 'message': str(e)}, status=500)

def update_delivery(request, delivery_id):
    try:
        if not ObjectId.is_valid(delivery_id):
            return JsonResponse({'error': 'Invalid delivery ID format'}, status=400)
        data = json.loads(request.body)
        data['updated_at'] = datetime.now().isoformat()
        if 'status' in data:
            valid_statuses = ['Ready for Pickup', 'Out for Delivery', 'Delivered', 'Cancelled']
            if data['status'] not in valid_statuses:
                return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        result = deliveries_collection.update_one(
            {'_id': ObjectId(delivery_id)},
            {'$set': data}
        )
        if result.matched_count == 0:
            return JsonResponse({'error': 'Delivery not found'}, status=404)
        updated_delivery = deliveries_collection.find_one({'_id': ObjectId(delivery_id)})
        updated_delivery['_id'] = str(updated_delivery['_id'])
        # Create invoice if delivery status is updated to 'Delivered'
        if data.get('status') == 'Delivered':
            create_invoice_from_delivery(updated_delivery)
        logger.info(f"Delivery updated successfully: {delivery_id}")
        return JsonResponse({
            'message': 'Delivery updated successfully',
            'delivery': updated_delivery
        }, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating delivery {delivery_id}: {e}")
        return JsonResponse({'error': 'Failed to update delivery', 'message': str(e)}, status=500)

def delete_delivery(request, delivery_id):
    try:
        if not ObjectId.is_valid(delivery_id):
            return JsonResponse({'error': 'Invalid delivery ID format'}, status=400)
        result = deliveries_collection.delete_one({'_id': ObjectId(delivery_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Delivery not found'}, status=404)
        logger.info(f"Delivery deleted successfully: {delivery_id}")
        return JsonResponse({'message': 'Delivery deleted successfully'}, status=200)
    except Exception as e:
        logger.error(f"Error deleting delivery {delivery_id}: {e}")
        return JsonResponse({'error': 'Failed to delete delivery', 'message': str(e)}, status=500)

# ========== INVOICE MANAGEMENT API ENDPOINTS ==========

def create_invoice_from_order(order):
    """Create an invoice from an order"""
    try:
        # Check if an invoice already exists for this order
        existing_invoice = invoices_collection.find_one({'order_id': order['_id']})
        if existing_invoice:
            logger.info(f"Invoice already exists for order {order['_id']}")
            return
        invoice_data = {
            'order_id': order['_id'],
            'customer_name': order['customer_name'],
            'date': order['created_at'].split('T')[0],  # Format as YYYY-MM-DD
            'amount': float(order['total']),
            'status': 'Unpaid' if order['status'] in ['Pending', 'Preparing', 'Ready'] else 'Paid',
            'items': order.get('items', []),  # Include order items for PDF
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        result = invoices_collection.insert_one(invoice_data)
        logger.info(f"Invoice created from order: {result.inserted_id}")
    except Exception as e:
        logger.error(f"Error creating invoice from order {order['_id']}: {e}")

def create_invoice_from_delivery(delivery):
    """Create an invoice from a delivery"""
    try:
        # Check if an invoice already exists for this delivery
        existing_invoice = invoices_collection.find_one({'delivery_id': delivery['_id']})
        if existing_invoice:
            logger.info(f"Invoice already exists for delivery {delivery['_id']}")
            return
        # Fetch associated order to get amount and items
        order = order_collection.find_one({'_id': ObjectId(delivery['order_id'])}) if ObjectId.is_valid(delivery['order_id']) else None
        invoice_data = {
            'delivery_id': delivery['_id'],
            'order_id': delivery['order_id'],
            'customer_name': delivery['customer_name'],
            'date': delivery['created_at'].split('T')[0],  # Format as YYYY-MM-DD
            'amount': float(order['total']) if order else 0.0,
            'status': 'Paid' if delivery['status'] == 'Delivered' else 'Unpaid',
            'items': order.get('items', []) if order else [],  # Include order items if available
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        result = invoices_collection.insert_one(invoice_data)
        logger.info(f"Invoice created from delivery: {result.inserted_id}")
    except Exception as e:
        logger.error(f"Error creating invoice from delivery {delivery['_id']}: {e}")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def invoices_api(request):
    if request.method == 'GET':
        return get_all_invoices(request)
    elif request.method == 'POST':
        return create_invoice(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def invoice_detail_api(request, invoice_id):
    if request.method == 'GET':
        return get_invoice(request, invoice_id)
    elif request.method == 'PUT':
        return update_invoice(request, invoice_id)
    elif request.method == 'DELETE':
        return delete_invoice(request, invoice_id)

@require_http_methods(["GET"])
def invoice_pdf(request, invoice_id):
    """Generate PDF for a specific invoice using LaTeX"""
    try:
        if not ObjectId.is_valid(invoice_id):
            return JsonResponse({'error': 'Invalid invoice ID format'}, status=400)
        
        invoice = invoices_collection.find_one({'_id': ObjectId(invoice_id)})
        if not invoice:
            return JsonResponse({'error': 'Invoice not found'}, status=404)
        
        # Generating LaTeX code for the invoice
        latex_content = r"""
        \documentclass[a4paper]{article}
        \usepackage[utf8]{inputenc}
        \usepackage{geometry}
        \usepackage{array}
        \usepackage{booktabs}
        \usepackage{parskip}
        \geometry{margin=1in}
        \begin{document}
        \begin{center}
            \textbf{\Large Invoice} \\
            \vspace{0.5cm}
        \end{center}
        \noindent
        \textbf{Invoice \#:} """ + str(invoice['_id']) + r""" \\
        \textbf{Customer:} """ + invoice['customer_name'] + r""" \\
        \textbf{Date:} """ + invoice['date'] + r""" \\
        \textbf{Amount:} \$""" + f"{invoice['amount']:.2f}" + r""" \\
        \textbf{Status:} """ + invoice['status'] + r""" \\
        \vspace{0.5cm}
        \begin{center}
            \textbf{Order Details}
        \end{center}
        \begin{tabular}{p{5cm} p{3cm} p{2cm} p{3cm}}
            \toprule
            \textbf{Item} & \textbf{Price} & \textbf{Quantity} & \textbf{Total} \\
            \midrule
        """
        for item in invoice.get('items', []):
            total = float(item['price']) * int(item['quantity'])
            latex_content += f"    {item['name']} & \${item['price']} & {item['quantity']} & \${total:.2f} \\\\ \n"
        latex_content += r"""
            \bottomrule
        \end{tabular}
        \vspace{0.5cm}
        \noindent
        \textbf{Total Amount:} \$""" + f"{invoice['amount']:.2f}" + r""" \\
        \end{document}
        """
        
        # Writing LaTeX content to a temporary file
        latex_file_path = f"/tmp/invoice_{invoice_id}.tex"
        pdf_file_path = f"/tmp/invoice_{invoice_id}.pdf"
        with open(latex_file_path, 'w') as f:
            f.write(latex_content)
        
        # Compiling LaTeX to PDF using pdflatex
        try:
            subprocess.run(
                ['latexmk', '-pdf', '-pdflatex=pdflatex', latex_file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error compiling LaTeX for invoice {invoice_id}: {e.stderr}")
            return JsonResponse({'error': 'Failed to generate PDF', 'message': str(e)}, status=500)
        
        # Reading the generated PDF
        with open(pdf_file_path, 'rb') as f:
            pdf_data = f.read()
        
        # Cleaning up temporary files
        for ext in ['.tex', '.pdf', '.aux', '.log', '.fls', '.fdb_latexmk']:
            try:
                os.remove(f"/tmp/invoice_{invoice_id}{ext}")
            except FileNotFoundError:
                pass
        
        # Returning the PDF
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
        return response
    
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {invoice_id}: {e}")
        return JsonResponse({'error': 'Failed to generate PDF', 'message': str(e)}, status=500)

def get_all_invoices(request):
    try:
        status = request.GET.get('status')
        customer_name = request.GET.get('customer_name')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        query = {}
        if status:
            query['status'] = status
        if customer_name:
            query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
        invoices_cursor = invoices_collection.find(query).sort('created_at', -1).limit(limit).skip(skip)
        invoices = []
        for invoice in invoices_cursor:
            invoice['_id'] = str(invoice['_id'])
            if 'created_at' not in invoice:
                invoice['created_at'] = datetime.now().isoformat()
            invoices.append(invoice)
        return JsonResponse(invoices, safe=False, status=200)
    except Exception as e:
        logger.error(f"Error retrieving invoices: {e}")
        return JsonResponse({'error': 'Failed to retrieve invoices', 'message': str(e)}, status=500)


def create_invoice(request):
    try:
        data = json.loads(request.body)
        required_fields = ['customer_name', 'date', 'amount', 'status', 'payment_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        try:
            amount = float(data['amount'])
            if amount < 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Amount must be a non-negative number'}, status=400)
        valid_statuses = ['Paid', 'Unpaid']
        if data['status'] not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        valid_payment_types = ['Cash', 'Credit Card', 'Online Payment']
        if data['payment_type'] not in valid_payment_types:
            return JsonResponse({'error': f'Invalid payment type. Must be one of: {valid_payment_types}'}, status=400)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        result = invoices_collection.insert_one(data)
        data['_id'] = str(result.inserted_id)
        logger.info(f"Invoice created successfully: {result.inserted_id}")
        return JsonResponse({
            'message': 'Invoice created successfully',
            'invoice_id': str(result.inserted_id),
            'invoice': data
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        return JsonResponse({'error': 'Failed to create invoice', 'message': str(e)}, status=500)

def update_invoice(request, invoice_id):
    try:
        if not ObjectId.is_valid(invoice_id):
            return JsonResponse({'error': 'Invalid invoice ID format'}, status=400)
        data = json.loads(request.body)
        data['updated_at'] = datetime.now().isoformat()
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount < 0:
                    raise ValueError
            except ValueError:
                return JsonResponse({'error': 'Amount must be a non-negative number'}, status=400)
        if 'status' in data:
            valid_statuses = ['Paid', 'Unpaid']
            if data['status'] not in valid_statuses:
                return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        if 'payment_type' in data:
            valid_payment_types = ['Cash', 'Credit Card', 'Online Payment']
            if data['payment_type'] not in valid_payment_types:
                return JsonResponse({'error': f'Invalid payment type. Must be one of: {valid_payment_types}'}, status=400)
        result = invoices_collection.update_one(
            {'_id': ObjectId(invoice_id)},
            {'$set': data}
        )
        if result.matched_count == 0:
            return JsonResponse({'error': 'Invoice not found'}, status=404)
        updated_invoice = invoices_collection.find_one({'_id': ObjectId(invoice_id)})
        updated_invoice['_id'] = str(updated_invoice['_id'])
        logger.info(f"Invoice updated successfully: {invoice_id}")
        return JsonResponse({
            'message': 'Invoice updated successfully',
            'invoice': updated_invoice
        }, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {e}")
        return JsonResponse({'error': 'Failed to update invoice', 'message': str(e)}, status=500)

def get_invoice(request, invoice_id):
    try:
        if not ObjectId.is_valid(invoice_id):
            return JsonResponse({'error': 'Invalid invoice ID format'}, status=400)
        invoice = invoices_collection.find_one({'_id': ObjectId(invoice_id)})
        if not invoice:
            return JsonResponse({'error': 'Invoice not found'}, status=404)
        invoice['_id'] = str(invoice['_id'])
        return JsonResponse(invoice, status=200)
    except Exception as e:
        logger.error(f"Error retrieving invoice {invoice_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve invoice', 'message': str(e)}, status=500)

def delete_invoice(request, invoice_id):
    try:
        if not ObjectId.is_valid(invoice_id):
            return JsonResponse({'error': 'Invalid invoice ID format'}, status=400)
        result = invoices_collection.delete_one({'_id': ObjectId(invoice_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Invoice not found'}, status=404)
        logger.info(f"Invoice deleted successfully: {invoice_id}")
        return JsonResponse({'message': 'Invoice deleted successfully'}, status=200)
    except Exception as e:
        logger.error(f"Error deleting invoice {invoice_id}: {e}")
        return JsonResponse({'error': 'Failed to delete invoice', 'message': str(e)}, status=500)