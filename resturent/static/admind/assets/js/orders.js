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


        fetch('/add-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'  // Django or Flask CSRF token
            },
            body: JSON.stringify({ customer, time, status })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });

        // Add to table directly (Frontend only)
        const tbody = document.getElementById('order-processing-tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>#NEW</td>
            <td>${customer}</td>
            <td>${time}</td>
            <td><span class="badge status-${status.toLowerCase()}">${status}</span></td>
            <td class="text-center">
                <button class="btn btn-sm btn-info-custom me-1 view-order-details-btn">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-sm btn-secondary" disabled>
                    <i class="fas fa-clock"></i> Waiting
                </button>
            </td>
        `;
        tbody.prepend(newRow);

        addOrderModal.hide();
        addOrderForm.reset();
    });

    // Delete Order (if delete buttons exist)
    const deleteButtons = document.querySelectorAll('.delete-order-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const orderId = this.dataset.id;

            fetch(`/delete-order/${orderId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': '{{ csrf_token }}' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert("Failed to delete the order.");
                }
            });
        });
    });
});
