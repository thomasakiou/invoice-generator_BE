class ReceiptGenerator {
    constructor() {
        this.items = [];
        this.logoFile = null;
        this.signatureFile = null;
        this.currentCurrency = 'USD';
        this.currencySymbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CAD': '$',
            'AUD': '$', 'CHF': '₣', 'CNY': '¥', 'INR': '₹', 'KRW': '₩',
            'NGN': '₦', 'ZAR': 'R', 'BRL': 'R$', 'MXN': '$', 'SGD': '$',
            'HKD': '$', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'RUB': '₽'
        };
        window.receiptGenerator = this;
        this.init();
    }

    init() {
        this.generateReceiptNumber();
        this.setDefaultDate();
        this.addInitialItem();
        this.setupEventListeners();
        this.calculateTotals();
    }

    setupEventListeners() {
        // Currency change
        document.getElementById('currency').addEventListener('change', (e) => {
            this.currentCurrency = e.target.value;
            this.updateAllItemTotals();
            this.calculateTotals();
        });

        // Add item button
        document.getElementById('addItemBtn').addEventListener('click', () => {
            this.addItem();
        });

        // Tax and discount inputs
        document.getElementById('taxRate').addEventListener('input', () => {
            this.calculateTotals();
        });

        document.getElementById('discountRate').addEventListener('input', () => {
            this.calculateTotals();
        });

        // Generate and preview buttons
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateReceipt();
        });

        document.getElementById('previewBtn').addEventListener('click', () => {
            this.previewReceipt();
        });

        // File uploads
        this.setupFileUploads();
    }

    setupFileUploads() {
        // Logo upload
        const logoUpload = document.getElementById('logoUpload');
        const logoArea = logoUpload.parentElement;
        
        logoArea.addEventListener('click', () => logoUpload.click());
        logoArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            logoArea.style.borderColor = '#4a90e2';
        });
        logoArea.addEventListener('dragleave', () => {
            logoArea.style.borderColor = '#ddd';
        });
        logoArea.addEventListener('drop', (e) => {
            e.preventDefault();
            logoArea.style.borderColor = '#ddd';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleLogoUpload(files[0]);
            }
        });
        
        logoUpload.addEventListener('change', (e) => {
            console.log('Receipt logo file input changed', e.target.files);
            if (e.target.files && e.target.files.length > 0) {
                console.log('Calling receipt handleLogoUpload');
                this.handleLogoUpload(e.target.files[0]);
            }
        });

        // Signature upload
        const signatureUpload = document.getElementById('signatureUpload');
        const signatureArea = signatureUpload.parentElement;
        
        signatureArea.addEventListener('click', () => signatureUpload.click());
        signatureArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            signatureArea.style.borderColor = '#4a90e2';
        });
        signatureArea.addEventListener('dragleave', () => {
            signatureArea.style.borderColor = '#ddd';
        });
        signatureArea.addEventListener('drop', (e) => {
            e.preventDefault();
            signatureArea.style.borderColor = '#ddd';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleSignatureUpload(files[0]);
            }
        });
        
        signatureUpload.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                this.handleSignatureUpload(e.target.files[0]);
            }
        });
    }

    generateReceiptNumber() {
        const now = new Date();
        const receiptNumber = `REC-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
        document.getElementById('receiptNumber').value = receiptNumber;
    }

    setDefaultDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('paymentDate').value = today;
    }

    addInitialItem() {
        this.addItem();
    }

    addItem() {
        const itemsContainer = document.getElementById('itemsList');
        const itemIndex = this.items.length;
        
        const itemRow = document.createElement('div');
        itemRow.className = 'item-row';
        itemRow.innerHTML = `
            <input type="text" placeholder="Enter item description" class="item-description" data-index="${itemIndex}">
            <input type="number" placeholder="Qty" min="0" step="0.01" class="item-quantity" data-index="${itemIndex}">
            <input type="number" placeholder="Price" min="0" step="0.01" class="item-price" data-index="${itemIndex}">
            <div class="item-total">$0.00</div>
            ${itemIndex === 0 ? '' : `<button type="button" class="remove-item-btn remove-item" data-index="${itemIndex}"><i class="fas fa-trash"></i></button>`}
        `;
        
        itemsContainer.appendChild(itemRow);
        
        this.items.push({
            description: '',
            quantity: 0,
            unit_price: 0
        });
        
        this.setupItemEventListeners(itemIndex);
    }

    setupItemEventListeners(index) {
        const itemRow = document.querySelector(`[data-index="${index}"]`).parentElement;
        
        itemRow.querySelector('.item-description').addEventListener('input', (e) => {
            this.items[index].description = e.target.value;
        });
        
        itemRow.querySelector('.item-quantity').addEventListener('input', (e) => {
            this.items[index].quantity = parseFloat(e.target.value) || 0;
            this.updateItemTotal(index);
            this.calculateTotals();
        });
        
        itemRow.querySelector('.item-price').addEventListener('input', (e) => {
            this.items[index].unit_price = parseFloat(e.target.value) || 0;
            this.updateItemTotal(index);
            this.calculateTotals();
        });
        
        const removeBtn = itemRow.querySelector('.remove-item');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.items.splice(index, 1);
                this.rebuildItemsList();
                this.calculateTotals();
            });
        }
    }

    updateItemTotal(index) {
        const item = this.items[index];
        const total = item.quantity * item.unit_price;
        const itemRow = document.querySelector(`[data-index="${index}"]`).parentElement;
        const symbol = this.currencySymbols[this.currentCurrency];
        itemRow.querySelector('.item-total').textContent = `${symbol} ${this.formatNumber(total)}`;
    }

    rebuildItemsList() {
        const itemsContainer = document.getElementById('itemsList');
        itemsContainer.innerHTML = '';
        this.items.forEach((item, index) => {
            const itemRow = document.createElement('div');
            itemRow.className = 'item-row';
            itemRow.innerHTML = `
                <input type="text" placeholder="Enter item description" class="item-description" data-index="${index}" value="${item.description}">
                <input type="number" placeholder="Qty" min="0" step="0.01" class="item-quantity" data-index="${index}" value="${item.quantity ? item.quantity : ''}">
                <input type="number" placeholder="Price" min="0" step="0.01" class="item-price" data-index="${index}" value="${item.unit_price ? item.unit_price : ''}">
                <div class="item-total">${this.currencySymbols[this.currentCurrency]} ${this.formatNumber(item.quantity * item.unit_price)}</div>
                ${index === 0 ? '' : `<button type="button" class="remove-item-btn remove-item" data-index="${index}"><i class="fas fa-trash"></i></button>`}
            `;
            
            itemsContainer.appendChild(itemRow);
            this.setupItemEventListeners(index);
        });
    }

    calculateTotals() {
        const subtotal = this.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
        const discountRate = parseFloat(document.getElementById('discountRate').value) || 0;
        const taxRate = parseFloat(document.getElementById('taxRate').value) || 0;
        
        const discountAmount = subtotal * (discountRate / 100);
        const afterDiscount = subtotal - discountAmount;
        const taxAmount = afterDiscount * (taxRate / 100);
        const total = afterDiscount + taxAmount;
        
        const symbol = this.currencySymbols[this.currentCurrency];
        
        document.getElementById('subtotalAmount').textContent = `${symbol} ${this.formatNumber(subtotal)}`;
        document.getElementById('discountAmount').textContent = `-${symbol} ${this.formatNumber(discountAmount)}`;
        document.getElementById('taxAmount').textContent = `${symbol} ${this.formatNumber(taxAmount)}`;
        document.getElementById('totalAmount').textContent = `${symbol} ${this.formatNumber(total)}`;
        
        // Show/hide discount and tax rows
        document.getElementById('discountRow').style.display = discountRate > 0 ? 'flex' : 'none';
        document.getElementById('taxRow').style.display = taxRate > 0 ? 'flex' : 'none';
    }

    formatNumber(num) {
        return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    updateAllItemTotals() {
        this.items.forEach((item, index) => {
            this.updateItemTotal(index);
        });
    }

    handleLogoUpload(file) {
        console.log('Receipt logo upload started', file);
        
        if (!file) {
            console.error('No file provided');
            return;
        }
        
        // Check file size (150KB limit)
        const maxSize = 150 * 1024; // 150KB in bytes
        if (file.size > maxSize) {
            this.showMessage(`Logo file size must be less than 150KB. Current size: ${(file.size / 1024).toFixed(1)}KB`, 'error');
            return;
        }
        
        // Check file type
        if (!file.type.startsWith('image/')) {
            this.showMessage('Please select a valid image file for logo', 'error');
            return;
        }
        
        this.logoFile = file;
        const preview = document.getElementById('logoPreview');
        console.log('Receipt preview element found:', preview);
        
        if (!preview) {
            console.error('Missing preview element');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            console.log('Receipt file read complete');
            preview.innerHTML = `
                <div style="position: relative; display: inline-block;">
                    <img src="${e.target.result}" alt="Logo Preview" style="max-width: 200px; max-height: 100px; display: block;">
                    <button type="button" onclick="window.receiptGenerator.removeLogo()" 
                            style="position: absolute; bottom: 5px; right: 5px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            console.log('Receipt preview HTML set');
        };
        reader.onerror = (e) => {
            console.error('Receipt FileReader error:', e);
        };
        reader.readAsDataURL(file);
    }

    handleSignatureUpload(file) {
        // Check file size (150KB limit)
        const maxSize = 150 * 1024; // 150KB in bytes
        if (file.size > maxSize) {
            this.showMessage(`Signature file size must be less than 150KB. Current size: ${(file.size / 1024).toFixed(1)}KB`, 'error');
            return;
        }
        
        // Check file type
        if (!file.type.startsWith('image/')) {
            this.showMessage('Please select a valid image file for signature', 'error');
            return;
        }
        
        this.signatureFile = file;
        const preview = document.getElementById('signaturePreview');
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `
                <div style="position: relative; display: inline-block;">
                    <img src="${e.target.result}" alt="Signature Preview" style="max-width: 200px; max-height: 100px; display: block;">
                    <button type="button" onclick="window.receiptGenerator.removeSignature()" 
                            style="position: absolute; bottom: 5px; right: 5px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    }

    async generateReceipt() {
        if (!this.validateForm()) return;
        
        this.showLoading();
        
        try {
            const formData = this.collectFormData();
            const response = await fetch('./api/receipts/generate-pdf', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `receipt-${document.getElementById('receiptNumber').value}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showMessage('Receipt generated successfully!', 'success');
            } else {
                throw new Error('Failed to generate receipt');
            }
        } catch (error) {
            console.error('Error generating receipt:', error);
            this.showMessage('Error generating receipt. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async previewReceipt() {
        if (!this.validateForm()) return;
        
        this.showLoading();
        
        try {
            const formData = this.collectFormData();
            const response = await fetch('./api/receipts/generate-pdf', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('Failed to preview receipt');
            }
        } catch (error) {
            console.error('Error previewing receipt:', error);
            this.showMessage('Error previewing receipt. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    validateForm() {
        const requiredFields = ['companyName', 'receiptNumber', 'customerName', 'paymentDate', 'paymentMethod'];
        
        for (const fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                this.showMessage(`Please fill in the ${field.previousElementSibling.textContent}`, 'error');
                field.focus();
                return false;
            }
        }
        
        return true;
    }

    collectFormData() {
        const formData = new FormData();
        
        // Calculate totals
        const subtotal = this.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
        const discountRate = parseFloat(document.getElementById('discountRate').value) || 0;
        const taxRate = parseFloat(document.getElementById('taxRate').value) || 0;
        const discountAmount = subtotal * (discountRate / 100);
        const afterDiscount = subtotal - discountAmount;
        const taxAmount = afterDiscount * (taxRate / 100);
        const total = afterDiscount + taxAmount;
        
        // Basic receipt data
        const receiptData = {
            receipt_number: document.getElementById('receiptNumber').value,
            currency: document.getElementById('currency').value,
            currency_symbol: this.currencySymbols[document.getElementById('currency').value],
            company: {
                name: document.getElementById('companyName').value,
                services: document.getElementById('companyServices').value || null,
                address: document.getElementById('companyAddress').value,
                email: document.getElementById('companyEmail').value,
                phone: document.getElementById('companyPhone').value
            },
            customer_name: document.getElementById('customerName').value,
            customer_address: document.getElementById('customerAddress').value,
            payment_date: document.getElementById('paymentDate').value || null,
            payment_method: document.getElementById('paymentMethod').value,
            items: this.items.filter(item => item.description && item.quantity > 0),
            subtotal: subtotal,
            tax_rate: taxRate,
            tax_amount: taxAmount,
            discount_rate: discountRate,
            discount_amount: discountAmount,
            total: total,
            comments: document.getElementById('comments').value,
            template: document.getElementById('template').value,
            signature: {
                user_name: document.getElementById('userName').value,
                position: document.getElementById('userPosition').value
            }
        };
        
        console.log('Receipt data being sent:', receiptData);
        formData.append('receipt_data', JSON.stringify(receiptData));
        
        if (this.logoFile) {
            formData.append('logo', this.logoFile);
        }
        
        if (this.signatureFile) {
            formData.append('signature', this.signatureFile);
        }
        
        return formData;
    }

    showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showMessage(message, type) {
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 5000);
    }

    removeLogo() {
        this.logoFile = null;
        const preview = document.getElementById('logoPreview');
        if (preview) {
            preview.innerHTML = '';
        }
        const upload = document.getElementById('logoUpload');
        if (upload) {
            upload.value = '';
        }
    }

    removeSignature() {
        this.signatureFile = null;
        const preview = document.getElementById('signaturePreview');
        if (preview) {
            preview.innerHTML = '';
        }
        const upload = document.getElementById('signatureUpload');
        if (upload) {
            upload.value = '';
        }
    }
}

// Theme toggle functionality
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const body = document.body;
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
        themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    themeToggleBtn.addEventListener('click', () => {
        body.classList.toggle('dark-theme');
        const isDark = body.classList.contains('dark-theme');
        
        // Update icon
        themeToggleBtn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        
        // Save theme preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// Initialize the receipt generator when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.receiptGenerator = new ReceiptGenerator();
    initThemeToggle();
});