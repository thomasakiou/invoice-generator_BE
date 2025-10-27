// Invoice Generator JavaScript

class InvoiceGenerator {
    constructor() {
        this.items = [];
        this.logoFile = null;
        this.signatureFile = null;
        this.signatureFilename = null;
        this.currentCurrency = 'USD';
        this.currencySymbols = {
            USD: '$', EUR: '€', GBP: '£', JPY: '¥', CAD: '$', AUD: '$', 
            CHF: 'CHF', CNY: '¥', INR: 'INR', KRW: 'KRW', NGN: 'NGN', ZAR: 'R',
            BRL: 'R$', MXN: '$', SGD: '$', HKD: '$', SEK: 'kr', NOK: 'kr',
            DKK: 'kr', RUB: 'RUB'
        };
        
        // API base URL - change this if your FastAPI server runs on a different port
        this.baseURL = 'http://localhost:8000';
        
        this.init();
    }
    
    // Format number with comma separators (e.g., 1,000.00)
    formatNumber(number) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(number);
    }
    
    init() {
        this.preventFormSubmission();
        this.setupEventListeners();
        this.addInitialItem();
        this.setupFileUploads();
        this.generateInvoiceNumber();
        this.setDefaultDates();
        this.initializeCurrency();
    }
    
    preventFormSubmission() {
        // No form element exists anymore, so no form submission prevention needed
    }
    
    initializeCurrency() {
        this.currentCurrency = document.getElementById('currency').value;
        this.updateCurrencyDisplay();
    }
    
    setupEventListeners() {
        // Add item button
        document.getElementById('addItemBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.addItem();
        });
        
        // Form submission - only allow through specific buttons
        document.getElementById('invoiceForm').addEventListener('submit', (e) => {
            console.log('🚫 Form submit event prevented');
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
        
        // Preview button with simple onclick assignment
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            // Replace the button with a new one to ensure clean state
            const newPreviewBtn = previewBtn.cloneNode(true);
            newPreviewBtn.id = 'previewBtn';
            newPreviewBtn.type = 'button';
            previewBtn.parentNode.replaceChild(newPreviewBtn, previewBtn);
            
            // Set up preview button click handler
            newPreviewBtn.onclick = (e) => {
                
                e.preventDefault();
                e.stopPropagation();
                
                // Add visual feedback
                newPreviewBtn.disabled = true;
                newPreviewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                
                // Execute preview
                try {
                    this.previewInvoice();
                } catch (error) {
                    console.error('Error in previewInvoice:', error);
                    this.showMessage('Error generating preview: ' + error.message, 'error');
                } finally {
                    // Restore button
                    setTimeout(() => {
                        newPreviewBtn.disabled = false;
                        newPreviewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview PDF';
                    }, 2000);
                }
                
                return false;
            };
            

        } else {
            console.error('❌ Preview button not found!');
        }
        
        // Generate button with simple onclick assignment (bypasses all event system issues)
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            // Replace the button with a new one to ensure clean state
            const newGenerateBtn = generateBtn.cloneNode(true);
            newGenerateBtn.id = 'generateBtn';
            newGenerateBtn.type = 'button';
            generateBtn.parentNode.replaceChild(newGenerateBtn, generateBtn);
            
            // Set up generate button click handler
            newGenerateBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Add visual feedback
                newGenerateBtn.disabled = true;
                newGenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                
                // Execute generate
                setTimeout(() => {
                    try {
                        this.generateInvoice();
                    } catch (error) {
                        console.error('Error in generateInvoice:', error);
                    } finally {
                        // Restore button
                        setTimeout(() => {
                            newGenerateBtn.disabled = false;
                            newGenerateBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDF';
                        }, 2000);
                    }
                }, 100);
                
                return false;
            };
        } else {
            console.error('❌ Generate button not found!');
        }
        
        // Tax and discount rate changes
        document.getElementById('taxRate').addEventListener('input', () => {
            this.calculateTotals();
        });
        
        document.getElementById('discountRate').addEventListener('input', () => {
            this.calculateTotals();
        });
        
        // Currency change
        document.getElementById('currency').addEventListener('change', (e) => {
            this.currentCurrency = e.target.value;
            this.updateCurrencyDisplay();
            this.calculateTotals();
        });
        
        // Theme toggle logic
        const themeToggleBtn = document.getElementById('themeToggleBtn');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', function() {
                document.body.classList.toggle('dark-theme');
                if (document.body.classList.contains('dark-theme')) {
                    themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
                } else {
                    themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
                }
            });
            // Ensure only icon is shown on load
            themeToggleBtn.innerHTML = document.body.classList.contains('dark-theme')
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
        } else {
            console.error('❌ Theme toggle button not found!');
        }
    }
    
    setupFileUploads() {
        
        // COMPLETELY SAFE FILE UPLOAD APPROACH
        this.setupSafeFileUpload('logoUpload', 'logo');
        this.setupSafeFileUpload('signatureUpload', 'signature');
        
        // Logo upload
        const logoArea = logoUpload.parentElement;
        
        console.log('🔍 Logo upload element:', logoUpload);
        console.log('🔍 Logo area element:', logoArea);
        
        if (!logoUpload) {
            console.error('❌ Logo upload input not found!');
            return;
        }
        
        // Test if the element exists and is working
        logoUpload.addEventListener('click', () => {
            console.log('👆 Logo input clicked');
        });
        
        logoArea.addEventListener('click', () => {
            logoUpload.click();
        });
        
        logoArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            logoArea.style.borderColor = '#4a90e2';
            console.log('🎯 Drag over logo area');
        });
        
        logoArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            logoArea.style.borderColor = '#ddd';
        });
        
        logoArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            logoArea.style.borderColor = '#ddd';
            console.log('🎯 File dropped on logo area');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                console.log('📂 Dropped file:', files[0].name);
                this.handleLogoUpload(files[0]);
            }
        });
        
        // Completely isolated file handler - no interference
        logoUpload.addEventListener('change', (e) => {
            console.log('📁 LOGO FILE INPUT CHANGE - ISOLATED HANDLER');
            
            if (e.target.files && e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log('📂 Logo file selected:', file.name);
                
                // Store file immediately without any processing that could interfere
                this.logoFile = file;
                console.log('� Logo file stored directly in memory');
                
                // Create preview in completely isolated way
                this.createLogoPreviewIsolated(file);
                
                // Clear the input to prevent any residual issues
                setTimeout(() => {
                    e.target.value = '';
                }, 500);
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
            console.log('🖊️ SIGNATURE FILE INPUT CHANGE - ISOLATED HANDLER');
            
            if (e.target.files && e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log('📂 Signature file selected:', file.name);
                
                // Store file immediately without any processing that could interfere
                this.signatureFile = file;
                console.log('💾 Signature file stored directly in memory');
                
                // Create preview in completely isolated way
                this.createSignaturePreviewIsolated(file);
                
                // Clear the input to prevent any residual issues
                setTimeout(() => {
                    e.target.value = '';
                }, 500);
            }
        });
    }
    
    generateInvoiceNumber() {
        const now = new Date();
        const invoiceNumber = `INV-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
        document.getElementById('invoiceNumber').value = invoiceNumber;
    }
    
    setDefaultDates() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('purchaseDate').value = today;
        
        // Set due date to 30 days from now
        const dueDate = new Date();
        dueDate.setDate(dueDate.getDate() + 30);
        document.getElementById('dueDate').value = dueDate.toISOString().split('T')[0];
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
            <input type="text" placeholder="Enter item description (e.g., Web Design Service)" class="item-description" data-index="${itemIndex}">
            <input type="number" placeholder="Qty" min="0" step="0.01" class="item-quantity" data-index="${itemIndex}">
            <input type="number" placeholder="Price" min="0" step="0.01" class="item-price" data-index="${itemIndex}">
            <div class="item-total">$0.00</div>
            ${itemIndex === 0 ? '' : `<button type="button" class="remove-item-btn remove-item" data-index="${itemIndex}"><i class="fas fa-trash"></i></button>`}
        `;
        
        itemsContainer.appendChild(itemRow);
        
        // Add item to array
        this.items.push({
            description: '',
            quantity: 0,
            unit_price: 0
        });
        
        // Setup event listeners for this item
        this.setupItemEventListeners(itemIndex);
    }
    
    setupItemEventListeners(index) {
        const itemRow = document.querySelector(`[data-index="${index}"]`).parentElement;
        
        // Description input
        itemRow.querySelector('.item-description').addEventListener('input', (e) => {
            this.items[index].description = e.target.value;
        });
        
        // Quantity input
        itemRow.querySelector('.item-quantity').addEventListener('input', (e) => {
            this.items[index].quantity = parseFloat(e.target.value) || 0;
            this.updateItemTotal(index);
            this.calculateTotals();
        });
        
        // Price input
        itemRow.querySelector('.item-price').addEventListener('input', (e) => {
            this.items[index].unit_price = parseFloat(e.target.value) || 0;
            this.updateItemTotal(index);
            this.calculateTotals();
        });
        
        // Remove button
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
    
    removeItem(index) {
        // Remove from array
        this.items.splice(index, 1);
        
        // Remove from DOM and reindex
        this.rebuildItemsList();
        this.calculateTotals();
    }
    
    rebuildItemsList() {
        const itemsContainer = document.getElementById('itemsList');
        itemsContainer.innerHTML = '';
        this.items.forEach((item, index) => {
            const itemRow = document.createElement('div');
            itemRow.className = 'item-row';
            itemRow.innerHTML = `
                <input type="text" placeholder="Enter item description (e.g., Web Design Service)" class="item-description" data-index="${index}" value="${item.description}">
                <input type="number" placeholder="Qty" min="0" step="0.01" class="item-quantity" data-index="${index}" value="${item.quantity ? item.quantity : ''}">
                <input type="number" placeholder="Price" min="0" step="0.01" class="item-price" data-index="${index}" value="${item.unit_price ? item.unit_price : ''}">
                <div class="item-total">${this.currencySymbols[this.currentCurrency]}${this.formatNumber(item.quantity * item.unit_price)}</div>
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
        const taxableAmount = subtotal - discountAmount;
        const taxAmount = taxableAmount * (taxRate / 100);
        const total = taxableAmount + taxAmount;
        
        const symbol = this.currencySymbols[this.currentCurrency];
        
        // Update display
        document.getElementById('subtotalAmount').textContent = `${symbol} ${this.formatNumber(subtotal)}`;
        document.getElementById('discountAmount').textContent = `-${symbol} ${this.formatNumber(discountAmount)}`;
        document.getElementById('taxAmount').textContent = `${symbol} ${this.formatNumber(taxAmount)}`;
        document.getElementById('totalAmount').textContent = `${symbol} ${this.formatNumber(total)}`;
        
        // Show/hide rows
        document.getElementById('discountRow').style.display = discountRate > 0 ? 'flex' : 'none';
        document.getElementById('taxRow').style.display = taxRate > 0 ? 'flex' : 'none';
        
        return { subtotal, discountAmount, taxAmount, total };
    }
    
    updateCurrencyDisplay() {
        // Update all currency displays when currency changes
        this.calculateTotals();
        
        // Update item totals
        this.items.forEach((item, index) => {
            this.updateItemTotal(index);
        });
    }
    
    handleLogoUpload(file) {
        // Immediately prevent any default behavior
        console.log('🎯 handleLogoUpload called with file:', file ? file.name : 'null', file ? file.type : 'no type');
        
        try {
            if (!file || !file.type.startsWith('image/')) {
                console.log('❌ Invalid file type or no file');
                this.showMessage('Please select a valid image file for the logo.', 'error');
                return false;
            }
            
            console.log('✅ File is valid image, proceeding with upload');
            
            // Don't clear the file input immediately - this might be causing issues
            console.log('💾 Logo file stored, keeping file input value for now');
            
            // Store file reference
            this.logoFile = file;
            
            // Create persistent preview immediately
            const preview = document.getElementById('logoPreview');
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    // Create a persistent preview that won't disappear
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.alt = 'Logo Preview';
                    img.style.maxWidth = '100%';
                    img.style.maxHeight = '150px';
                    img.style.objectFit = 'contain';
                    
                    // Clear and add new preview
                    preview.innerHTML = '';
                    preview.appendChild(img);
                    preview.style.display = 'block';
                    
                    // Add a remove button
                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.innerHTML = '✕ Remove';
                    removeBtn.className = 'remove-preview-btn';
                    removeBtn.style.cssText = 'margin-top:5px;padding:2px 8px;background:#ff4757;color:white;border:none;border-radius:3px;cursor:pointer;font-size:12px;';
                    removeBtn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.removeLogo();
                        return false;
                    };
                    preview.appendChild(removeBtn);
                    
                    // Show success message in upload area
                    const logoArea = document.getElementById('logoUpload').parentElement;
                    const uploadText = logoArea.querySelector('.upload-text');
                    if (uploadText) {
                        uploadText.innerHTML = '<i class="fas fa-check" style="color: green;"></i><span style="color: green;">Logo uploaded successfully!</span>';
                    }
                    
                    this.showMessage('Logo preview loaded successfully!', 'success');
                } catch (err) {
                    console.error('Preview error:', err);
                    this.showMessage('Error displaying logo preview.', 'error');
                }
            };
            
            reader.onerror = (e) => {
                console.error('File reader error:', e);
                this.showMessage('Error reading file. Please try again.', 'error');
            };
            
            // Start reading the file
            reader.readAsDataURL(file);
            
            // Store the file data for PDF generation (no server upload needed)
            console.log('💾 Logo stored in memory for PDF generation');
            this.showMessage('Logo ready for PDF generation!', 'success');
            
        } catch (error) {
            console.error('Logo upload error:', error);
            this.showMessage('Error processing logo. Please try again.', 'error');
        }
        
        return false; // Always prevent default
    }
    
    setupSafeFileUpload(inputId, type) {
        const input = document.getElementById(inputId);
        if (!input) {
            console.log(`❌ File input ${inputId} not found`);
            return;
        }
        
        console.log(`🔧 Setting up SAFE ${type} upload for ${inputId}`);
        
        // Use the safest possible event handling - no aggressive prevention
        input.addEventListener('change', (e) => {
            console.log(`📁 SAFE ${type.toUpperCase()} UPLOAD - NO DOM INTERFERENCE`);
            
            if (e.target.files && e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log(`📂 ${type} file selected:`, file.name);
                
                // Store file with minimal impact
                if (type === 'logo') {
                    this.logoFile = file;
                } else if (type === 'signature') {
                    this.signatureFile = file;
                }
                
                // Create safe preview WITHOUT DOM manipulation that could affect buttons
                this.createSafePreview(inputId, file, type);
                
                console.log(`✅ ${type} stored safely`);
            }
        });
        
        console.log(`✅ Safe ${type} upload setup complete`);
    }
    
    createSafePreview(inputId, file, type) {
        try {
            const previewId = type === 'logo' ? 'logoPreview' : 'signaturePreview';
            const preview = document.getElementById(previewId);
            
            if (!preview) {
                console.log(`Preview element ${previewId} not found`);
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = (e) => {
                // Minimal DOM manipulation - just set innerHTML
                const maxHeight = type === 'logo' ? '150px' : '100px';
                preview.innerHTML = `<img src="${e.target.result}" alt="${type} preview" style="max-width:100%;max-height:${maxHeight};object-fit:contain;display:block;margin:5px 0;">`;
                preview.style.display = 'block';
                console.log(`✅ Safe ${type} preview created`);
            };
            
            reader.onerror = (e) => {
                console.error(`Error creating ${type} preview:`, e);
            };
            
            reader.readAsDataURL(file);
        } catch (error) {
            console.error(`Error in safe preview creation:`, error);
        }
    }
    
    createLogoPreviewIsolated(file) {
        console.log('🖼️ Creating isolated logo preview');
        try {
            const preview = document.getElementById('logoPreview');
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = 'Logo Preview';
                img.style.cssText = 'max-width:100%;max-height:150px;object-fit:contain;display:block;margin:10px 0;';
                
                preview.innerHTML = '';
                preview.appendChild(img);
                preview.style.display = 'block';
                
                console.log('✅ Logo preview created successfully');
            };
            
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('❌ Error creating logo preview:', error);
        }
    }
    
    createSignaturePreviewIsolated(file) {
        console.log('🖼️ Creating isolated signature preview');
        try {
            const preview = document.getElementById('signaturePreview');
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = 'Signature Preview';
                img.style.cssText = 'max-width:100%;max-height:100px;object-fit:contain;display:block;margin:10px 0;';
                
                preview.innerHTML = '';
                preview.appendChild(img);
                preview.style.display = 'block';
                
                console.log('✅ Signature preview created successfully');
            };
            
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('❌ Error creating signature preview:', error);
        }
    }
    
    removeLogo() {
        this.logoFile = null;
        const preview = document.getElementById('logoPreview');
        preview.innerHTML = '';
        preview.style.display = 'none';
        
        // Clear the file input
        const logoUpload = document.getElementById('logoUpload');
        logoUpload.value = '';
        
        // Restore original upload text
        const logoArea = logoUpload.parentElement;
        const uploadText = logoArea.querySelector('.upload-text');
        if (uploadText) {
            uploadText.innerHTML = '<i class="fas fa-upload"></i><span>Click to upload logo or drag & drop</span>';
        }
        
        this.showMessage('Logo removed.', 'info');
    }
    
    removeSignature() {
        this.signatureFile = null;
        this.signatureFilename = null;
        console.log('Signature removed - filename cleared:', this.signatureFilename);
        
        const preview = document.getElementById('signaturePreview');
        preview.innerHTML = '';
        preview.style.display = 'none';
        
        // Clear the file input
        const signatureUpload = document.getElementById('signatureUpload');
        signatureUpload.value = '';
        
        // Restore original upload text
        const signatureArea = signatureUpload.parentElement;
        const uploadText = signatureArea.querySelector('.upload-text');
        if (uploadText) {
            uploadText.innerHTML = '<i class="fas fa-pen-nib"></i><span>Click to upload signature or drag & drop</span>';
        }
        
        this.showMessage('Signature removed.', 'info');
    }
    
    handleSignatureUpload(file) {
        // Immediately prevent any default behavior
        console.log('🖊️ handleSignatureUpload called with file:', file ? file.name : 'null', file ? file.type : 'no type');
        try {
            if (!file || !file.type.startsWith('image/')) {
                console.log('❌ Invalid file type or no file');
                this.showMessage('Please select a valid image file for the signature.', 'error');
                return false;
            }
            
            console.log('✅ Signature file is valid, proceeding with processing');
            
            // Don't clear the signature file input immediately - this might be causing issues
            console.log('💾 Signature file stored, keeping file input value for now');
            
            // Store file reference
            this.signatureFile = file;
            
            // Create persistent preview immediately
            const preview = document.getElementById('signaturePreview');
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    // Create a persistent preview that won't disappear
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.alt = 'Signature Preview';
                    img.style.maxWidth = '100%';
                    img.style.maxHeight = '100px';
                    img.style.objectFit = 'contain';
                    
                    // Clear and add new preview
                    preview.innerHTML = '';
                    preview.appendChild(img);
                    preview.style.display = 'block';
                    
                    // Add a remove button
                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.innerHTML = '✕ Remove';
                    removeBtn.className = 'remove-preview-btn';
                    removeBtn.style.cssText = 'margin-top:5px;padding:2px 8px;background:#ff4757;color:white;border:none;border-radius:3px;cursor:pointer;font-size:12px;';
                    removeBtn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.removeSignature();
                        return false;
                    };
                    preview.appendChild(removeBtn);
                    
                    // Show success message in upload area
                    const signatureArea = document.getElementById('signatureUpload').parentElement;
                    const uploadText = signatureArea.querySelector('.upload-text');
                    if (uploadText) {
                        uploadText.innerHTML = '<i class="fas fa-check" style="color: green;"></i><span style="color: green;">Signature uploaded successfully!</span>';
                    }
                    
                    this.showMessage('Signature preview loaded successfully!', 'success');
                } catch (err) {
                    console.error('Preview error:', err);
                    this.showMessage('Error displaying signature preview.', 'error');
                }
            };
            
            reader.onerror = (e) => {
                console.error('File reader error:', e);
                this.showMessage('Error reading file. Please try again.', 'error');
            };
            
            // Start reading the file
            reader.readAsDataURL(file);
            
            // Store the file data for PDF generation (no server upload needed)
            console.log('💾 Signature stored in memory for PDF generation');
            this.showMessage('Signature ready for PDF generation!', 'success');
            
        } catch (error) {
            console.error('Signature upload error:', error);
            this.showMessage('Error processing signature. Please try again.', 'error');
        }
        
        return false; // Always prevent default
    }
    
    // Upload functions removed - now using temporary files sent directly with PDF generation
    
    validateForm() {
        console.log('🔍 Starting form validation...');
        const required = ['companyName', 'invoiceNumber', 'clientName'];
        let isValid = true;
        
        for (const fieldId of required) {
            const field = document.getElementById(fieldId);
            const value = field ? field.value.trim() : '';
            console.log(`📝 Checking field ${fieldId}: "${value}"`);
            
            if (!value) {
                console.log(`❌ Field ${fieldId} is empty`);
                if (field) field.style.borderColor = '#dc3545';
                isValid = false;
            } else {
                console.log(`✅ Field ${fieldId} is valid`);
                if (field) field.style.borderColor = '#ddd';
            }
        }
        
        // Check if at least one item exists
        console.log('📦 Checking items:', this.items.length, 'total items');
        const hasValidItems = this.items.length > 0 && this.items.some(item => item.description.trim());
        console.log('📦 Has valid items:', hasValidItems);
        
        if (!hasValidItems) {
            console.log('❌ No valid items found');
            this.showMessage('Please add at least one item to the invoice.', 'error');
            isValid = false;
        }
        
        if (!isValid) {
            console.log('❌ Form validation failed overall');
            this.showMessage('Please fill in all required fields.', 'error');
        } else {
            console.log('✅ Form validation passed');
        }
        
        return isValid;
    }
    
    getInvoiceData() {
        const totals = this.calculateTotals();
        const taxRate = parseFloat(document.getElementById('taxRate').value) || 0;
        const discountRate = parseFloat(document.getElementById('discountRate').value) || 0;
        
        const invoiceData = {
            invoice_number: document.getElementById('invoiceNumber').value,
            currency: document.getElementById('currency').value,
            currency_symbol: this.currencySymbols[this.currentCurrency],
            template: document.getElementById('template').value,
            company: {
                name: document.getElementById('companyName').value,
                address: document.getElementById('companyAddress').value || null,
                email: document.getElementById('companyEmail').value || null,
                phone: document.getElementById('companyPhone').value || null
            },
            client_name: document.getElementById('clientName').value,
            client_address: document.getElementById('clientAddress').value || null,
            items: this.items.filter(item => item.description.trim()),
            subtotal: totals.subtotal,
            tax_rate: taxRate > 0 ? taxRate : null,
            tax_amount: taxRate > 0 ? totals.taxAmount : null,
            discount_rate: discountRate > 0 ? discountRate : null,
            discount_amount: discountRate > 0 ? totals.discountAmount : null,
            total: totals.total,
            due_date: document.getElementById('dueDate').value || null,
            purchase_date: document.getElementById('purchaseDate').value || null,
            comments: document.getElementById('comments').value || null,
            signature: {
                user_name: document.getElementById('userName').value || null,
                position: document.getElementById('userPosition').value || null,
                signature_filename: null // Not using server files anymore
            }
        };
        
        // Debug log the signature data being sent
        console.log('Invoice data signature info:', {
            user_name: invoiceData.signature.user_name,
            position: invoiceData.signature.position,
            signature_filename: invoiceData.signature.signature_filename,
            stored_filename: this.signatureFilename
        });
        
        return invoiceData;
    }
    
    async generateInvoice() {
        console.log('🎯 generateInvoice called');
        
        if (!this.validateForm()) {
            console.log('❌ Form validation failed');
            return;
        }
        
        console.log('✅ Form validation passed');
        this.showLoading('Generating invoice...');
        
        try {
            const invoiceData = this.getInvoiceData();
            console.log('📋 Invoice data prepared:', invoiceData);
            
            // Create FormData to send invoice data with images
            const formData = new FormData();
            formData.append('invoice_data', JSON.stringify(invoiceData));
            
            // Add logo if available
            if (this.logoFile) {
                formData.append('logo', this.logoFile);
                console.log('📎 Adding logo to request:', this.logoFile.name);
            } else {
                console.log('📎 No logo file to add');
            }
            
            // Add signature if available
            if (this.signatureFile) {
                formData.append('signature', this.signatureFile);
                console.log('📎 Adding signature to request:', this.signatureFile.name);
            } else {
                console.log('📎 No signature file to add');
            }
            
            console.log('🚀 Sending PDF generation request to:', `${this.baseURL}/api/invoices/generate-pdf`);
            
            const response = await fetch(`${this.baseURL}/api/invoices/generate-pdf`, {
                method: 'POST',
                body: formData // Using FormData instead of JSON
            });
            
            console.log('📥 Response received:', response.status, response.statusText);
            
            if (response.ok) {
                console.log('✅ PDF generation successful, downloading...');
                // Download the PDF
                const blob = await response.blob();
                console.log('📄 PDF blob size:', blob.size, 'bytes');
                
                const url = window.URL.createObjectURL(blob);
                
                // Auto-download
                const a = document.createElement('a');
                a.href = url;
                a.download = `invoice_${invoiceData.invoice_number}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                // Manual backup button
                const downloadBtn = `<a href="${url}" download="invoice_${invoiceData.invoice_number}.pdf" style="display:inline-block;margin:10px;padding:8px 12px;background:#007bff;color:white;text-decoration:none;border-radius:4px;font-weight:bold;"><i class="fas fa-download"></i> Download Invoice</a>`;
                
                this.showMessage(`✅ Invoice ready! ${downloadBtn}<br/><small style="color:#666;">Invoice should download automatically. If not, click the blue button above.</small>`, 'success');
            } else {
                console.error('❌ PDF generation failed with status:', response.status);
                const errorText = await response.text();
                console.error('❌ Error response:', errorText);
                throw new Error(`Failed to generate invoice: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            console.error('💥 Invoice generation error:', error);
            this.showMessage(`Failed to generate invoice: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async previewInvoice() {
        console.log('👁️ previewInvoice function called');
        
        if (!this.validateForm()) {
            console.log('❌ Preview validation failed');
            return;
        }
        
        console.log('✅ Preview validation passed');
        this.showLoading('Generating preview...');
        
        try {
            const invoiceData = this.getInvoiceData();
            console.log('📋 Preview invoice data prepared');
            
            // Create FormData to send invoice data with images
            const formData = new FormData();
            formData.append('invoice_data', JSON.stringify(invoiceData));
            
            // Add logo if available
            if (this.logoFile) {
                formData.append('logo', this.logoFile);
                console.log('📎 Adding logo to preview request:', this.logoFile.name);
            } else {
                console.log('📎 No logo file for preview');
            }
            
            // Add signature if available
            if (this.signatureFile) {
                formData.append('signature', this.signatureFile);
                console.log('📎 Adding signature to preview request:', this.signatureFile.name);
            } else {
                console.log('📎 No signature file for preview');
            }
            
            console.log('🚀 Sending preview request...');
            
            const response = await fetch(`${this.baseURL}/api/invoices/generate-pdf`, {
                method: 'POST',
                body: formData
            });
            
            console.log('📥 Preview response received:', response.status, response.statusText);
            
            if (response.ok) {
                console.log('✅ Preview response OK, creating blob...');
                const blob = await response.blob();
                console.log('📄 Preview blob created, size:', blob.size, 'bytes');
                
                if (blob.size === 0) {
                    throw new Error('Received empty PDF blob');
                }
                
                // IMMEDIATE DOWNLOAD APPROACH - Most reliable
                console.log('� Triggering immediate PDF download...');
                const url = window.URL.createObjectURL(blob);
                
                // Open PDF in new window for preview (no download)
                const previewWindow = window.open(url, '_blank', 'width=900,height=700,scrollbars=yes,resizable=yes,toolbar=no,menubar=no,location=no');
                
                // Manual backup button
                const downloadBtn = `<a href="${url}" download="invoice_${invoiceData.invoice_number}_preview.pdf" style="display:inline-block;margin:10px;padding:8px 12px;background:#28a745;color:white;text-decoration:none;border-radius:4px;font-weight:bold;"><i class="fas fa-download"></i> Download PDF</a>`;
                
                console.log('✅ PDF download triggered');
                if (previewWindow && !previewWindow.closed) {
                    console.log('✅ PDF preview opened in new window');
                    const downloadBtn = `<a href="${url}" download="invoice_${invoiceData.invoice_number}_preview.pdf" style="display:inline-block;margin:10px;padding:8px 12px;background:#28a745;color:white;text-decoration:none;border-radius:4px;font-weight:bold;"><i class="fas fa-download"></i> Download PDF</a>`;
                    this.showMessage(`✅ PDF preview opened! ${downloadBtn}<br/><small style="color:#666;">Preview opened in new window. Use the button above to download if needed.</small>`, 'success');
                } else {
                    console.log('⚠️ Popup blocked, providing manual options');
                    const downloadBtn = `<a href="${url}" download="invoice_${invoiceData.invoice_number}_preview.pdf" style="display:inline-block;margin:10px;padding:8px 12px;background:#28a745;color:white;text-decoration:none;border-radius:4px;font-weight:bold;"><i class="fas fa-download"></i> Download PDF</a>`;
                    const viewBtn = `<a href="${url}" target="_blank" style="display:inline-block;margin:10px;padding:8px 12px;background:#007bff;color:white;text-decoration:none;border-radius:4px;font-weight:bold;"><i class="fas fa-eye"></i> View PDF</a>`;
                    this.showMessage(`📋 PDF ready! ${viewBtn} ${downloadBtn}<br/><small style="color:#666;">Popup was blocked. Click "View PDF" to preview or "Download PDF" to save.</small>`, 'success');
                }
                
                // Also try popup as secondary option
                console.log('🪟 Also attempting popup window...');
                setTimeout(() => {
                    try {
                        const previewWindow = window.open(url, '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
                        if (previewWindow && !previewWindow.closed) {
                            console.log('✅ Popup window also opened');
                            this.showMessage('✅ PDF downloaded AND opened in new window!', 'success');
                        }
                    } catch (e) {
                        console.log('ℹ️ Popup failed but download succeeded');
                    }
                }, 100);
                
                // Clean up URL after delay
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    console.log('🧹 Preview blob URL cleaned up');
                }, 30000);
            } else {
                console.error('❌ Preview request failed:', response.status);
                const errorText = await response.text();
                console.error('❌ Error response:', errorText);
                throw new Error(`Failed to generate preview: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            console.error('Preview error:', error);
            this.showMessage('Failed to generate preview. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    downloadPdfFromBlob(blob, invoiceNumber) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `invoice_${invoiceNumber}_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.showMessage('Invoice downloaded successfully!', 'success');
    }
    
    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = overlay.querySelector('p');
        text.textContent = message;
        overlay.style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
    
    showMessage(message, type = 'info') {
        const container = document.getElementById('messageContainer');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            ${message}
            <button class="message-close">&times;</button>
        `;
        
        container.appendChild(messageDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 5000);
        
        // Close button
        messageDiv.querySelector('.message-close').addEventListener('click', () => {
            messageDiv.remove();
        });
    }
}

// Add debugging to catch page unload
window.addEventListener('beforeunload', (e) => {
    console.log('🚨 PAGE IS ABOUT TO RELOAD/UNLOAD!');
    console.trace('Stack trace of what caused the reload:');
    // Uncomment the next line to prevent the reload and see what's causing it
    // e.preventDefault();
    // return 'Page is reloading - check console for cause';
});

// Initialize when DOM is loaded - no form exists so no form prevention needed
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 Initializing without form element...');
    
    // Add click debugging (non-intrusive)
    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            console.log('🖱️ BUTTON CLICK DETECTED:', {
                target: e.target,
                tagName: e.target.tagName,
                id: e.target.id,
                type: e.target.type,
                classList: Array.from(e.target.classList),
                textContent: e.target.textContent.substring(0, 50)
            });
            
            // Special logging for our main buttons
            if (e.target.id === 'previewBtn') {
                console.log('🎯 PREVIEW BUTTON CLICKED!');
            } else if (e.target.id === 'generateBtn') {
                console.log('🎯 GENERATE BUTTON CLICKED!');
            } else {
                console.log('ℹ️ Other button clicked:', e.target.textContent.substring(0, 30));
            }
        }
    });
    
    // Initialize the invoice generator
    new InvoiceGenerator();
});