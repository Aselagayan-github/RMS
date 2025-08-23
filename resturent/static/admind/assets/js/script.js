// JavaScript for handling Orders in the Restaurant Admin Panel
document.addEventListener('DOMContentLoaded', function () {
    // Open the Bootstrap Modal
    const addBookingBtn = document.getElementById('addNewBookingBtn');
    const addOrderModalEl = document.getElementById('addOrderModal');
    const addOrderModal = new bootstrap.Modal(addOrderModalEl);

    addBookingBtn.addEventListener('click', function () {
        addOrderModal.show();
    });

    // Handle Add Order Form Submission
    const addOrderForm = document.getElementById('addOrderForm');
    addOrderForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const customer = document.getElementById('customerName').value.trim();
        const time = document.getElementById('orderTime').value.trim();
        const status = document.getElementById('orderStatus').value;

        if (!customer || !time || !status) {
            alert("Please fill out all fields.");
            return;
        }

        // Send to backend
        fetch('/api/orders/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ 
                customer_name: customer,
                order_type: 'Dine-in',  // Default order_type
                items: [],  // Empty items allowed now
                status: status,
                order_time: time  // Extra field, will be saved in MongoDB
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                alert('Order created successfully! ID: ' + data.order_id);
                location.reload();
            } else {
                alert("Failed to create the order: " + data.error);
            }
        }).catch(error => {
            console.error('Error:', error);
            alert("Error creating order.");
        });

        addOrderModal.hide();
        addOrderForm.reset();
    });

    // Delete Order
    const deleteButtons = document.querySelectorAll('.delete-order-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const orderId = this.dataset.id;

            fetch(`/api/orders/${orderId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            })
            .then(res => res.json())
            .then(data => {
                if (data.message) {
                    alert("Order deleted successfully.");
                    location.reload();
                } else {
                    alert("Failed to delete the order.");
                }
            }).catch(error => {
                console.error('Error:', error);
                alert("Error deleting order.");
            });
        });
    });

    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
