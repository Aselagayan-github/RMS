document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('#main-menu a');
    const views = document.querySelectorAll('.content-area .view');
    const currentViewTitle = document.getElementById('current-view-title');
    const themeToggleButton = document.getElementById('theme-toggle');
    const themeToggleIcon = themeToggleButton?.querySelector('i');

    const THEME_KEY = 'dashboard-theme';
    let userPieChartInstance = null;
    let salesBarChartInstance = null;

    // Chart color definitions
    const lightModeChartColors = { backgrounds: ['rgba(26, 188, 156, 0.85)','rgba(52, 152, 219, 0.85)','rgba(243, 156, 18, 0.85)'], borders: ['rgba(22, 160, 133, 1)','rgba(41, 128, 185, 1)','rgba(211, 84, 0, 1)'], legendText: '#555', tooltipBg: 'rgba(255,255,255,0.95)', tooltipTitle: '#333', tooltipBody: '#555', tooltipBorder: 'rgba(200,200,200,0.9)', gridColor: 'rgba(0,0,0,0.1)' };
    const darkModeChartColors = { backgrounds: ['rgba(80, 250, 123, 0.8)','rgba(108, 92, 231, 0.8)','rgba(0, 206, 209, 0.8)'], borders: ['rgba(60, 220, 103, 1)','rgba(88, 72, 211, 1)','rgba(0, 186, 189, 1)'], legendText: 'var(--text-color)', tooltipBg: 'rgba(40,40,70,0.95)', tooltipTitle: '#eee', tooltipBody: '#ddd', tooltipBorder: 'rgba(100,100,150,0.9)', gridColor: 'rgba(255,255,255,0.1)' };

    // --- CORE APP LOGIC ---

    function updateChartTheme(isDark) {
        const newColors = isDark ? darkModeChartColors : lightModeChartColors;
        [userPieChartInstance, salesBarChartInstance].forEach(chartInstance => {
            if (chartInstance) {
                chartInstance.data.datasets.forEach(dataset => {
                    dataset.backgroundColor = newColors.backgrounds;
                    dataset.borderColor = newColors.borders;
                });
                if (chartInstance.options?.plugins?.legend) { chartInstance.options.plugins.legend.labels.color = newColors.legendText; }
                if (chartInstance.options?.plugins?.tooltip) {
                    Object.assign(chartInstance.options.plugins.tooltip, { backgroundColor: newColors.tooltipBg, titleColor: newColors.tooltipTitle, bodyColor: newColors.tooltipBody, borderColor: newColors.tooltipBorder });
                }
                if (chartInstance.options?.scales?.x) { chartInstance.options.scales.x.ticks.color = newColors.legendText; chartInstance.options.scales.x.grid.color = newColors.gridColor; }
                if (chartInstance.options?.scales?.y) { chartInstance.options.scales.y.ticks.color = newColors.legendText; chartInstance.options.scales.y.grid.color = newColors.gridColor; }
                chartInstance.update();
            }
        });
    }

    function setTheme(isDark) {
        document.body.classList.toggle('dark-mode', isDark);
        if (themeToggleIcon) {
            themeToggleIcon.classList.toggle('fa-sun', isDark);
            themeToggleIcon.classList.toggle('fa-moon', !isDark);
        }
        localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
        // Update charts only if their respective views are active
        if (document.getElementById('dashboard-view')?.classList.contains('active-view') || document.getElementById('sales-reports-view')?.classList.contains('active-view')) {
            updateChartTheme(isDark);
        }
    }

    if (themeToggleButton) { themeToggleButton.addEventListener('click', () => setTheme(!document.body.classList.contains('dark-mode'))); }
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(savedTheme === 'dark' || (savedTheme === null && prefersDarkScheme));

    function switchView(viewId, clickedLink) {
        const linkText = Array.from(clickedLink.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.textContent.trim()).join('');
        currentViewTitle.textContent = linkText || 'Dashboard';
        navLinks.forEach(link => link.classList.remove('active-menu'));
        views.forEach(view => view.classList.remove('active-view'));
        clickedLink.classList.add('active-menu');
        const targetView = document.getElementById(viewId + "-view");

        if (targetView) {
            targetView.classList.add('active-view');
            // Call the correct initializer for the new view
            if (viewId === 'dashboard') initializeDashboardWidgets();
            else if (viewId === 'user-management') initializeUserManagement();
            else if (viewId === 'offers-discounts') initializeOffersDiscounts();
            else if (viewId === 'order-processing') initializeOrderProcessing();
            else if (viewId === 'table-bookings') initializeTableBookings();
            else if (viewId === 'menu-management') initializeMenuManagement();
            else if (viewId === 'delivery-management') initializeDeliveryManagement();
            else if (viewId === 'invoice-management') initializeInvoiceManagement();
            else if (viewId === 'sales-reports') initializeSalesReports();
            else if (viewId === 'customer-feedback') initializeCustomerFeedback();
            else if (viewId === 'settings') initializeSettings();
            else if (viewId === 'logout') initializeLogout();
        } else {
            // Fallback to dashboard if view not found
            console.warn(`View with ID '${viewId}-view' not found.`);
            const defaultDashboardView = document.getElementById('dashboard-view');
            const dashboardLink = document.querySelector('a[data-view="dashboard"]');
            if (defaultDashboardView && dashboardLink) {
                defaultDashboardView.classList.add('active-view');
                dashboardLink.classList.add('active-menu');
                currentViewTitle.textContent = "Dashboard";
                initializeDashboardWidgets();
            }
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const viewId = link.getAttribute('data-view');
            if (viewId) {
                switchView(viewId, link);
            }
        });
    });
    
    // --- INITIALIZER FUNCTIONS FOR EACH VIEW ---

    function initializeDashboardWidgets() {
        const dashboardView = document.getElementById('dashboard-view');
        if (!dashboardView || dashboardView.dataset.widgetsInitialized === 'true') {
            if (dashboardView?.dataset.widgetsInitialized === 'true') updateChartTheme(document.body.classList.contains('dark-mode'));
            return;
        }
        const pieChartCtx = document.getElementById('userPieChart')?.getContext('2d');
        if (pieChartCtx && !userPieChartInstance) {
            const currentColors = document.body.classList.contains('dark-mode') ? darkModeChartColors : lightModeChartColors;
            userPieChartInstance = new Chart(pieChartCtx, {
                type: 'pie', data: { labels: ['Admin', 'Customer', 'Staff'], datasets: [{ label: 'User Distribution', data: [5, 55, 12], backgroundColor: currentColors.backgrounds, borderColor: currentColors.borders, borderWidth: 1.5, hoverOffset: 8 }] },
                options: { responsive: true, maintainAspectRatio: false, animation: { animateScale: true, animateRotate: true }, plugins: { legend: { position: 'bottom', labels: { color: currentColors.legendText, padding: 20, usePointStyle: true, pointStyle: 'circle', font: { size: 13, family: 'var(--font-secondary)' } } }, tooltip: { enabled: true, backgroundColor: currentColors.tooltipBg, titleColor: currentColors.tooltipTitle, titleFont: { family: 'var(--font-secondary)', weight: '600', size: 14 }, bodyColor: currentColors.tooltipBody, bodyFont: { family: 'var(--font-primary)', size: 13 }, borderColor: currentColors.tooltipBorder, borderWidth: 1, padding: 10, cornerRadius: 6, boxPadding: 3, callbacks: { label: function(context) { let label = context.label || ''; if (label) { label += ': '; } if (context.parsed !== null) { const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0); const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) + '%' : '0%'; label += `${context.parsed} (${percentage})`; } return label; } } } } }
            });
        } else if (userPieChartInstance) { updateChartTheme(document.body.classList.contains('dark-mode')); }
        fetchWeatherData();
        dashboardView.dataset.widgetsInitialized = 'true';
    }

    async function fetchWeatherData() { /* Kept as is from original prompt */ }
    function initializeUserManagement() { /* Kept as is from original prompt */ }
    function initializeOffersDiscounts() { /* Kept as is from original prompt */ }

    // --- NEW INITIALIZER FUNCTIONS ---

    function initializeOrderProcessing() {
        const view = document.getElementById('order-processing-view');
        if (!view || view.dataset.initialized === 'true') return;
        
        const orderTbody = view.querySelector('#order-processing-tbody');
        if (!orderTbody) return;

        orderTbody.addEventListener('click', (e) => {
            const updateBtn = e.target.closest('.update-order-status-btn');
            if (!updateBtn) return;
            
            const row = updateBtn.closest('tr');
            const statusBadge = row.querySelector('.badge');
            let currentStatus = statusBadge.textContent.trim();
            
            if (currentStatus === 'Pending') {
                statusBadge.textContent = 'Preparing';
                statusBadge.className = 'badge status-preparing';
                updateBtn.innerHTML = '<i class="fas fa-check-circle"></i> Mark Ready';
                updateBtn.classList.remove('btn-primary-custom');
                updateBtn.classList.add('btn-success-custom');
            } else if (currentStatus === 'Preparing') {
                statusBadge.textContent = 'Completed';
                statusBadge.className = 'badge status-completed';
                updateBtn.innerHTML = '<i class="fas fa-history"></i> Done';
                updateBtn.disabled = true;
                updateBtn.classList.remove('btn-success-custom');
                updateBtn.classList.add('btn-secondary');
            }
        });

        view.dataset.initialized = 'true';
    }

    function initializeTableBookings() {
        const view = document.getElementById('table-bookings-view');
        if (!view || view.dataset.initialized === 'true') return;

        const bookingModalEl = document.getElementById('bookingModal');
        const bookingModal = new bootstrap.Modal(bookingModalEl);
        const bookingForm = document.getElementById('bookingForm');
        const bookingsTbody = document.getElementById('bookings-tbody');
        const addNewBtn = document.getElementById('addNewBookingBtn');
        const modalLabel = document.getElementById('bookingModalLabel');
        const saveBtn = document.getElementById('saveBookingBtn');
        
        let editingRow = null;
        let nextBookingId = 3;

        addNewBtn.addEventListener('click', () => {
            editingRow = null;
            bookingForm.reset();
            document.getElementById('bookingId').value = `BK-${String(nextBookingId).padStart(3, '0')}`;
            modalLabel.textContent = 'Add New Booking';
            saveBtn.textContent = 'Add Booking';
            bookingModal.show();
        });

        bookingsTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-booking-btn');
            const deleteBtn = e.target.closest('.delete-booking-btn');
            
            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.querySelectorAll('td');
                document.getElementById('bookingId').value = cells[0].textContent;
                document.getElementById('bookingCustomerName').value = cells[1].textContent;
                const [date, time] = cells[2].textContent.split(', ');
                document.getElementById('bookingDate').value = date;
                document.getElementById('bookingTime').value = time;
                document.getElementById('bookingGuests').value = cells[3].textContent;
                document.getElementById('bookingStatus').value = cells[4].textContent;
                
                modalLabel.textContent = 'Edit Booking';
                saveBtn.textContent = 'Save Changes';
                bookingModal.show();
            }

            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                const bookingName = row.querySelector('td:nth-child(2)').textContent;
                if (confirm(`Are you sure you want to delete the booking for ${bookingName}?`)) {
                    row.remove();
                }
            }
        });

        bookingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const id = document.getElementById('bookingId').value;
            const name = document.getElementById('bookingCustomerName').value;
            const date = document.getElementById('bookingDate').value;
            const time = document.getElementById('bookingTime').value;
            const guests = document.getElementById('bookingGuests').value;
            const status = document.getElementById('bookingStatus').value;
            
            const statusBadgeClass = `status-${status.toLowerCase()}`;

            if (editingRow) { // Update
                const cells = editingRow.querySelectorAll('td');
                cells[0].textContent = id;
                cells[1].textContent = name;
                cells[2].textContent = `${date}, ${time}`;
                cells[3].textContent = guests;
                cells[4].innerHTML = `<span class="badge ${statusBadgeClass}">${status}</span>`;
            } else { // Create
                const newRow = bookingsTbody.insertRow();
                newRow.innerHTML = `
                    <td>${id}</td>
                    <td>${name}</td>
                    <td>${date}, ${time}</td>
                    <td>${guests}</td>
                    <td><span class="badge ${statusBadgeClass}">${status}</span></td>
                    <td class="text-center">
                        <button class="btn btn-icon btn-sm btn-primary-custom me-1 edit-booking-btn"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-icon btn-sm btn-danger-custom delete-booking-btn"><i class="fas fa-trash-alt"></i></button>
                    </td>`;
                nextBookingId++;
            }
            bookingModal.hide();
        });
        
        view.dataset.initialized = 'true';
    }

    function initializeMenuManagement() {
        const view = document.getElementById('menu-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        const menuItemModal = new bootstrap.Modal(document.getElementById('menuItemModal'));
        const menuItemForm = document.getElementById('menuItemForm');
        const menuItemsTbody = document.getElementById('menu-items-tbody');
        const addNewBtn = document.getElementById('addNewMenuItemBtn');
        
        let editingRow = null;

        addNewBtn.addEventListener('click', () => {
            editingRow = null;
            menuItemForm.reset();
            document.getElementById('menuItemId').value = '';
            document.getElementById('menuItemModalLabel').textContent = 'Add New Menu Item';
            menuItemModal.show();
        });

        menuItemsTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-menu-item-btn');
            const deleteBtn = e.target.closest('.delete-menu-item-btn');

            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.querySelectorAll('td');
                document.getElementById('menuItemName').value = cells[0].textContent;
                document.getElementById('menuItemCategory').value = cells[1].textContent;
                document.getElementById('menuItemPrice').value = parseFloat(cells[2].textContent.replace('$', ''));
                document.getElementById('menuItemAvailability').value = cells[3].textContent;
                document.getElementById('menuItemModalLabel').textContent = 'Edit Menu Item';
                menuItemModal.show();
            }
            
            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                if (confirm(`Delete item "${row.cells[0].textContent}"?`)) {
                    row.remove();
                }
            }
        });

        menuItemForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('menuItemName').value;
            const category = document.getElementById('menuItemCategory').value;
            const price = parseFloat(document.getElementById('menuItemPrice').value).toFixed(2);
            const availability = document.getElementById('menuItemAvailability').value;
            const availabilityBadge = availability === 'Available' ? '<span class="badge bg-success-custom">Available</span>' : '<span class="badge bg-secondary-custom">Unavailable</span>';

            if (editingRow) {
                const cells = editingRow.querySelectorAll('td');
                cells[0].textContent = name;
                cells[1].textContent = category;
                cells[2].textContent = `$${price}`;
                cells[3].innerHTML = availabilityBadge;
            } else {
                const newRow = menuItemsTbody.insertRow();
                newRow.innerHTML = `
                    <td>${name}</td>
                    <td>${category}</td>
                    <td>$${price}</td>
                    <td>${availabilityBadge}</td>
                    <td class="text-center">
                        <button class="btn btn-icon btn-sm btn-primary-custom me-1 edit-menu-item-btn"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-icon btn-sm btn-danger-custom delete-menu-item-btn"><i class="fas fa-trash-alt"></i></button>
                    </td>
                `;
            }
            menuItemModal.hide();
        });

        view.dataset.initialized = 'true';
    }
    
    function initializeDeliveryManagement() {
        const view = document.getElementById('delivery-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        view.querySelector('#delivery-tbody').addEventListener('click', (e) => {
            const assignBtn = e.target.closest('.assign-driver-btn');
            const updateBtn = e.target.closest('.update-delivery-status-btn');
            
            if (assignBtn) {
                const driverCell = assignBtn.closest('tr').querySelector('td:nth-child(4)');
                const statusCell = assignBtn.closest('tr').querySelector('td:nth-child(5) .badge');
                const newDriver = prompt("Enter driver's name:", "Sarah");
                if (newDriver) {
                    driverCell.textContent = newDriver;
                    statusCell.textContent = 'Out for Delivery';
                    statusCell.className = 'badge status-out-for-delivery';
                    assignBtn.textContent = 'Mark Delivered';
                    assignBtn.classList.remove('btn-primary-custom', 'assign-driver-btn');
                    assignBtn.classList.add('btn-success-custom', 'update-delivery-status-btn');
                }
            }
            if (updateBtn) {
                const statusCell = updateBtn.closest('tr').querySelector('td:nth-child(5) .badge');
                statusCell.textContent = 'Delivered';
                statusCell.className = 'badge status-delivered';
                updateBtn.textContent = 'Completed';
                updateBtn.disabled = true;
                updateBtn.classList.remove('btn-success-custom');
                updateBtn.classList.add('btn-secondary');
            }
        });

        view.dataset.initialized = 'true';
    }

    function initializeInvoiceManagement() {
        const view = document.getElementById('invoice-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        const generateBtn = document.getElementById('generateInvoiceBtn');
        const invoicesTbody = document.getElementById('invoices-tbody');
        let nextInvoiceNum = 3;

        generateBtn.addEventListener('click', () => {
            const newRow = invoicesTbody.insertRow(0);
            const invoiceNum = `INV-2024-${String(nextInvoiceNum++).padStart(3,'0')}`;
            newRow.innerHTML = `
                <td>${invoiceNum}</td>
                <td>New Customer</td>
                <td>${new Date().toISOString().slice(0, 10)}</td>
                <td>$0.00</td>
                <td><span class="badge status-unpaid">Unpaid</span></td>
                <td class="text-center">
                    <button class="btn btn-icon btn-sm btn-info-custom"><i class="fas fa-eye"></i></button> 
                    <button class="btn btn-icon btn-sm btn-secondary-custom"><i class="fas fa-print"></i></button>
                </td>`;
            alert(`Generated new invoice: ${invoiceNum}. You can now edit its details.`);
        });

        view.dataset.initialized = 'true';
    }

    function initializeSalesReports() {
        const view = document.getElementById('sales-reports-view');
        if (!view || view.dataset.initialized === 'true') {
             if (view?.dataset.initialized === 'true') updateChartTheme(document.body.classList.contains('dark-mode'));
            return;
        }

        const chartCtx = document.getElementById('salesBarChart')?.getContext('2d');
        if (chartCtx && !salesBarChartInstance) {
            const currentColors = document.body.classList.contains('dark-mode') ? darkModeChartColors : lightModeChartColors;
            salesBarChartInstance = new Chart(chartCtx, {
                type: 'bar',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Weekly Sales',
                        data: [1200, 1900, 1500, 2100, 1800, 2500, 2200],
                        backgroundColor: currentColors.backgrounds[1],
                        borderColor: currentColors.borders[1],
                        borderWidth: 1.5,
                        borderRadius: 5,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: currentColors.gridColor }, ticks: { color: currentColors.legendText } },
                        x: { grid: { color: currentColors.gridColor }, ticks: { color: currentColors.legendText } }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: { /* same as dashboard tooltip */ }
                    }
                }
            });
        } else if (salesBarChartInstance) { updateChartTheme(document.body.classList.contains('dark-mode')); }
        
        view.dataset.initialized = 'true';
    }

    function initializeCustomerFeedback() {
        const view = document.getElementById('customer-feedback-view');
        if (!view || view.dataset.initialized === 'true') return;
        
        view.querySelector('#feedback-list').addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.delete-feedback-btn');
            if(deleteBtn) {
                const card = deleteBtn.closest('.col-lg-6');
                if(confirm('Are you sure you want to delete this feedback?')){
                    card.remove();
                }
            }
        });

        view.dataset.initialized = 'true';
    }
    
    function initializeSettings() {
        const view = document.getElementById('settings-view');
        if (!view || view.dataset.initialized === 'true') return;
        
        document.getElementById('settingsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Settings saved successfully!');
            // In a real app, this would send data to a server.
        });

        view.dataset.initialized = 'true';
    }

    function initializeLogout() {
        const view = document.getElementById('logout-view');
        if (!view || view.dataset.initialized === 'true') return;

        const dashboardLink = document.querySelector('a[data-view="dashboard"]');
        document.getElementById('confirmLogoutBtn').addEventListener('click', () => {
            alert('You have been logged out.');
            // Here you would redirect to a login page, e.g., window.location.href = '/login';
        });
        document.getElementById('cancelLogoutBtn').addEventListener('click', () => {
            if (dashboardLink) {
                switchView('dashboard', dashboardLink);
            }
        });
        view.dataset.initialized = 'true';
    }

    // Initial load
    const defaultActiveLink = document.querySelector('#main-menu a.active-menu') || document.querySelector('#main-menu a[data-view="dashboard"]');
    if (defaultActiveLink) {
        switchView(defaultActiveLink.getAttribute('data-view'), defaultActiveLink);
    }
});

// Dummy implementations to avoid errors if original script parts are removed
async function fetchWeatherData() {
    const weatherWidget = document.getElementById('weatherWidget');
    if (!weatherWidget) return;
    weatherWidget.innerHTML = `<p class="weather-loading">Weather data loading is for demonstration.</p>`;
}
function initializeUserManagement() { /* Dummy function */ }
function initializeOffersDiscounts() { /* Dummy function */ }


document.addEventListener('DOMContentLoaded', () => {
    // --- CORE APP LOGIC ---
    const navLinks = document.querySelectorAll('#main-menu a');
    const views = document.querySelectorAll('.content-area .view');
    const currentViewTitle = document.getElementById('current-view-title');
    const themeToggleButton = document.getElementById('theme-toggle');
    const themeToggleIcon = themeToggleButton?.querySelector('i');
    let userPieChartInstance = null;
    let salesBarChartInstance = null;

    function updateChartTheme(isDark) { /* ... (as provided before) ... */ }
    function setTheme(isDark) { /* ... (as provided before) ... */ }
    if (themeToggleButton) { themeToggleButton.addEventListener('click', () => setTheme(!document.body.classList.contains('dark-mode'))); }
    // ... (theme loading logic as provided before) ...

    function switchView(viewId, clickedLink) {
        const linkText = Array.from(clickedLink.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.textContent.trim()).join('');
        currentViewTitle.textContent = linkText || 'Dashboard';
        navLinks.forEach(link => link.classList.remove('active-menu'));
        views.forEach(view => view.classList.remove('active-view'));
        clickedLink.classList.add('active-menu');
        const targetView = document.getElementById(viewId + "-view");

        if (targetView) {
            targetView.classList.add('active-view');
            // Call the correct initializer for the new view
            if (viewId === 'dashboard') initializeDashboardWidgets();
            else if (viewId === 'user-management') initializeUserManagement();
            else if (viewId === 'offers-discounts') initializeOffersDiscounts();
            else if (viewId === 'order-processing') initializeOrderProcessing();
            else if (viewId === 'table-bookings') initializeTableBookings();
            else if (viewId === 'menu-management') initializeMenuManagement();
            else if (viewId === 'delivery-management') initializeDeliveryManagement();
            else if (viewId === 'invoice-management') initializeInvoiceManagement();
            else if (viewId === 'sales-reports') initializeSalesReports();
            else if (viewId === 'customer-feedback') initializeCustomerFeedback();
            else if (viewId === 'settings') initializeSettings();
            else if (viewId === 'logout') initializeLogout();
        } else {
            // Fallback to dashboard if view not found
            console.warn(`View with ID '${viewId}-view' not found.`);
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const viewId = link.getAttribute('data-view');
            if (viewId) switchView(viewId, link);
        });
    });
    
    // --- INITIALIZER FUNCTIONS FOR EACH VIEW ---

    function initializeDashboardWidgets() { /* ... (as provided before) ... */ }
    async function fetchWeatherData() { /* ... (as provided before) ... */ }
    
    function initializeUserManagement() {
        const view = document.getElementById('user-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        const userModal = new bootstrap.Modal(document.getElementById('userModal'));
        const userForm = document.getElementById('userForm');
        const usersTbody = document.getElementById('users-tbody');
        const addNewBtn = document.getElementById('addNewUserBtn');
        const modalLabel = document.getElementById('userModalLabel');
        const passwordInput = document.getElementById('userPassword');
        
        let editingRow = null;
        let nextUserId = 3;

        addNewBtn.addEventListener('click', () => {
            editingRow = null;
            userForm.reset();
            document.getElementById('userId').value = '';
            document.getElementById('userIdDisplay').value = nextUserId;
            modalLabel.querySelector('i').className = 'fas fa-user-plus me-2';
            modalLabel.childNodes[1].textContent = ' Add New User';
            passwordInput.setAttribute('required', 'required');
            userModal.show();
        });

        usersTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.update-user-btn');
            const deleteBtn = e.target.closest('.delete-user-btn');

            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.cells;
                document.getElementById('userId').value = cells[0].textContent;
                document.getElementById('userIdDisplay').value = cells[0].textContent;
                document.getElementById('userName').value = cells[1].textContent;
                document.getElementById('userAddress').value = cells[2].textContent;
                document.getElementById('userContactNo').value = cells[3].textContent;
                document.getElementById('userEmail').value = cells[4].textContent;
                document.getElementById('userRole').value = cells[5].textContent;
                passwordInput.removeAttribute('required');
                modalLabel.querySelector('i').className = 'fas fa-user-edit me-2';
                modalLabel.childNodes[1].textContent = ' Edit User Information';
                userModal.show();
            }

            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                if (confirm(`Delete user "${row.cells[1].textContent}"?`)) row.remove();
            }
        });

        userForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const role = document.getElementById('userRole').value;
            const roleBadgeClass = role === 'Admin' ? 'bg-primary-custom' : (role === 'Staff' ? 'bg-info text-dark' : 'bg-secondary-custom');
            
            const rowData = `
                <td>${document.getElementById('userIdDisplay').value}</td>
                <td>${document.getElementById('userName').value}</td>
                <td>${document.getElementById('userAddress').value}</td>
                <td>${document.getElementById('userContactNo').value}</td>
                <td>${document.getElementById('userEmail').value}</td>
                <td><span class="badge ${roleBadgeClass}">${role}</span></td>
                <td class="text-center">
                    <button class="btn btn-icon btn-sm btn-primary-custom me-1 update-user-btn" title="Edit User"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-icon btn-sm btn-danger-custom delete-user-btn" title="Delete User"><i class="fas fa-trash-alt"></i></button>
                </td>`;
            
            if (editingRow) {
                editingRow.innerHTML = rowData;
            } else {
                const newRow = usersTbody.insertRow();
                newRow.innerHTML = rowData;
                nextUserId++;
            }
            userModal.hide();
        });

        view.dataset.initialized = 'true';
    }

    function initializeOffersDiscounts() {
        const view = document.getElementById('offers-discounts-view');
        if (!view || view.dataset.initialized === 'true') return;

        const addOfferBtn = view.querySelector('.btn-add-offer');
        const addFormContainer = view.querySelector('#add-offer-form-container');
        const addOfferForm = view.querySelector('#add-offer-form');
        const cancelAddBtn = view.querySelector('#cancel-add-offer-btn');
        const offersTbody = view.querySelector('#offers-tbody');
        const editOfferModal = new bootstrap.Modal(document.getElementById('editOfferModal'));
        const editOfferForm = document.getElementById('edit-offer-form');
        
        let editingRow = null;
        let nextOfferId = 4;

        function getStatusBadge(status) {
            const statusMap = {
                'active': 'bg-success-custom',
                'inactive': 'bg-secondary-custom',
                'expired': 'bg-secondary-custom',
                'upcoming': 'status-upcoming'
            };
            return `<span class="badge ${statusMap[status.toLowerCase()] || 'bg-secondary-custom'}">${status}</span>`;
        }

        addOfferBtn.addEventListener('click', () => {
            addFormContainer.style.display = 'block';
            addOfferBtn.style.display = 'none';
        });

        cancelAddBtn.addEventListener('click', () => {
            addFormContainer.style.display = 'none';
            addOfferBtn.style.display = 'inline-block';
            addOfferForm.reset();
        });

        addOfferForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(addOfferForm);
            const discount = formData.get('discountType') === 'Percentage' ? `${formData.get('discountValue')}%` : `$${formData.get('discountValue')}`;
            const newRow = offersTbody.insertRow();
            newRow.dataset.offerId = nextOfferId++;
            newRow.innerHTML = `
                <td>${formData.get('offerName')}</td>
                <td>${discount}</td>
                <td>${formData.get('startDate')}</td>
                <td>${formData.get('endDate')}</td>
                <td>${getStatusBadge(formData.get('offerStatus'))}</td>
                <td class="text-center">
                    <button class="btn btn-icon btn-sm btn-primary-custom me-1 edit-offer-btn" title="Edit Offer"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-icon btn-sm btn-danger-custom delete-offer-btn" title="Delete Offer"><i class="fas fa-trash-alt"></i></button>
                </td>`;
            cancelAddBtn.click();
        });

        offersTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-offer-btn');
            const deleteBtn = e.target.closest('.delete-offer-btn');

            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.cells;
                document.getElementById('edit-offer-id').value = editingRow.dataset.offerId;
                document.getElementById('edit-offer-name').value = cells[0].textContent;
                
                const discountText = cells[1].textContent;
                if (discountText.includes('%')) {
                    document.getElementById('edit-discount-type').value = 'Percentage';
                    document.getElementById('edit-discount-value').value = parseFloat(discountText);
                } else {
                    document.getElementById('edit-discount-type').value = 'Fixed Amount';
                    document.getElementById('edit-discount-value').value = parseFloat(discountText.replace('$', ''));
                }
                document.getElementById('edit-start-date').value = cells[2].textContent;
                document.getElementById('edit-end-date').value = cells[3].textContent;
                document.getElementById('edit-offer-status').value = cells[4].textContent;
                editOfferModal.show();
            }
            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                if (confirm(`Delete offer "${row.cells[0].textContent}"?`)) row.remove();
            }
        });

        editOfferForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (!editingRow) return;
            const formData = new FormData(editOfferForm);
            const discount = formData.get('discountType') === 'Percentage' ? `${formData.get('discountValue')}%` : `$${formData.get('discountValue')}`;
            editingRow.cells[0].textContent = formData.get('offerName');
            editingRow.cells[1].textContent = discount;
            editingRow.cells[2].textContent = formData.get('startDate');
            editingRow.cells[3].textContent = formData.get('endDate');
            editingRow.cells[4].innerHTML = getStatusBadge(formData.get('offerStatus'));
            editOfferModal.hide();
        });

        view.dataset.initialized = 'true';
    }
    
    function initializeOrderProcessing() { /* ... (as provided before) ... */ }
    function initializeTableBookings() { /* ... (as provided before) ... */ }

    function initializeMenuManagement() {
        const view = document.getElementById('menu-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        const menuItemModal = new bootstrap.Modal(document.getElementById('menuItemModal'));
        const menuItemForm = document.getElementById('menuItemForm');
        const menuItemsTbody = document.getElementById('menu-items-tbody');
        const addNewBtn = document.getElementById('addNewMenuItemBtn');
        const imageInput = document.getElementById('menuItemImage');
        const imagePreview = document.getElementById('menuItemImagePreview');

        let editingRow = null;
        const defaultImageUrl = 'https://placehold.co/200x200/cccccc/969696?text=Image';

        imageInput.addEventListener('change', () => {
            const file = imageInput.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => { imagePreview.src = e.target.result; };
                reader.readAsDataURL(file);
            }
        });

        addNewBtn.addEventListener('click', () => {
            editingRow = null;
            menuItemForm.reset();
            imageInput.value = '';
            imagePreview.src = defaultImageUrl;
            document.getElementById('menuItemModalLabel').textContent = 'Add New Menu Item';
            menuItemModal.show();
        });

        menuItemsTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-menu-item-btn');
            const deleteBtn = e.target.closest('.delete-menu-item-btn');

            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.cells;
                imagePreview.src = cells[0].querySelector('img').src;
                document.getElementById('menuItemName').value = cells[1].textContent;
                document.getElementById('menuItemCategory').value = cells[2].textContent;
                document.getElementById('menuItemPrice').value = parseFloat(cells[3].textContent.replace('$', ''));
                document.getElementById('menuItemAvailability').value = cells[4].textContent;
                document.getElementById('menuItemModalLabel').textContent = 'Edit Menu Item';
                imageInput.value = '';
                menuItemModal.show();
            }

            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                if (confirm(`Delete item "${row.cells[1].textContent}"?`)) row.remove();
            }
        });

        menuItemForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('menuItemName').value;
            const availability = document.getElementById('menuItemAvailability').value;
            const availabilityBadge = `<span class="badge ${availability === 'Available' ? 'bg-success-custom' : 'bg-secondary-custom'}">${availability}</span>`;
            
            const rowData = `
                <td><img src="${imagePreview.src}" class="menu-item-image" alt="${name}"></td>
                <td>${name}</td>
                <td>${document.getElementById('menuItemCategory').value}</td>
                <td>$${parseFloat(document.getElementById('menuItemPrice').value).toFixed(2)}</td>
                <td>${availabilityBadge}</td>
                <td class="text-center">
                    <button class="btn btn-icon btn-sm btn-primary-custom me-1 edit-menu-item-btn"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-icon btn-sm btn-danger-custom delete-menu-item-btn"><i class="fas fa-trash-alt"></i></button>
                </td>`;

            if (editingRow) {
                editingRow.innerHTML = rowData;
            } else {
                menuItemsTbody.insertRow().innerHTML = rowData;
            }
            menuItemModal.hide();
        });
        view.dataset.initialized = 'true';
    }
    
    function initializeDeliveryManagement() {
        const view = document.getElementById('delivery-management-view');
        if (!view || view.dataset.initialized === 'true') return;

        const deliveryModal = new bootstrap.Modal(document.getElementById('deliveryModal'));
        const deliveryForm = document.getElementById('deliveryForm');
        const deliveryTbody = document.getElementById('delivery-tbody');
        const addNewBtn = document.getElementById('addNewDeliveryBtn');
        const modalLabel = document.getElementById('deliveryModalLabel');
        let editingRow = null;
        let nextDeliveryId = 57;

        function getStatusBadge(status) {
            const statusClass = `status-${status.toLowerCase().replace(/ /g, '-')}`;
            return `<span class="badge ${statusClass}">${status}</span>`;
        }

        addNewBtn.addEventListener('click', () => {
            editingRow = null;
            deliveryForm.reset();
            document.getElementById('deliveryId').value = `D-${nextDeliveryId++}`;
            modalLabel.textContent = 'Add New Delivery';
            deliveryModal.show();
        });

        deliveryTbody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-delivery-btn');
            const deleteBtn = e.target.closest('.delete-delivery-btn');

            if (editBtn) {
                editingRow = editBtn.closest('tr');
                const cells = editingRow.cells;
                document.getElementById('deliveryId').value = editingRow.dataset.deliveryId;
                document.getElementById('deliveryOrderId').value = cells[0].textContent;
                document.getElementById('deliveryCustomerName').value = cells[1].textContent;
                document.getElementById('deliveryAddress').value = cells[2].textContent;
                document.getElementById('deliveryDriver').value = cells[3].textContent;
                document.getElementById('deliveryStatus').value = cells[4].textContent;
                modalLabel.textContent = 'Edit Delivery Details';
                deliveryModal.show();
            }

            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                if (confirm(`Delete delivery for order ${row.cells[0].textContent}?`)) row.remove();
            }
        });

        deliveryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const id = document.getElementById('deliveryId').value;
            const status = document.getElementById('deliveryStatus').value;
            const rowData = `
                <td>${document.getElementById('deliveryOrderId').value}</td>
                <td>${document.getElementById('deliveryCustomerName').value}</td>
                <td>${document.getElementById('deliveryAddress').value}</td>
                <td>${document.getElementById('deliveryDriver').value}</td>
                <td>${getStatusBadge(status)}</td>
                <td class="text-center">
                    <button class="btn btn-icon btn-sm btn-primary-custom me-1 edit-delivery-btn"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-icon btn-sm btn-danger-custom delete-delivery-btn"><i class="fas fa-trash-alt"></i></button>
                </td>`;

            if (editingRow) {
                editingRow.innerHTML = rowData;
                editingRow.dataset.deliveryId = id;
            } else {
                const newRow = deliveryTbody.insertRow();
                newRow.dataset.deliveryId = id;
                newRow.innerHTML = rowData;
            }
            deliveryModal.hide();
        });
        view.dataset.initialized = 'true';
    }

    function initializeInvoiceManagement() { /* ... (as provided before) ... */ }
    function initializeSalesReports() { /* ... (as provided before) ... */ }
    function initializeCustomerFeedback() { /* ... (as provided before) ... */ }
    function initializeSettings() { /* ... (as provided before) ... */ }
    function initializeLogout() { /* ... (as provided before) ... */ }

    // Initial load
    const defaultActiveLink = document.querySelector('#main-menu a.active-menu') || document.querySelector('#main-menu a[data-view="dashboard"]');
    if (defaultActiveLink) {
        switchView(defaultActiveLink.getAttribute('data-view'), defaultActiveLink);
    }
});