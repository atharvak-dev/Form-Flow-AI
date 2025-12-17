from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any, Optional
import asyncio
from asyncio import TimeoutError
import re
from speech_service import SpeechService

async def get_form_schema(url: str, generate_speech: bool = True, wait_for_dynamic: bool = True) -> Dict[str, Any]:
    """
    Enhanced form scraper with Google Forms support and advanced field detection
    
    Args:
        url: Target URL to scrape
        generate_speech: Whether to generate speech for form fields
        wait_for_dynamic: Whether to wait for dynamic content to load
    """
    fields = []
    is_google_form = 'docs.google.com/forms' in url
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Changed to False for better debugging
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--window-size=1920,1080"
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                geolocation={"longitude": -74.006, "latitude": 40.7128},
                permissions=["geolocation"],
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            )
            
            # Enhanced stealth scripts
            await context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                    ]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Mock chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add connection rtt
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => 100
                });
            """)
            
            page = await context.new_page()
            
            # Only block heavy resources
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in {"media", "font"} 
                else route.continue_())

            print(f"🔗 Navigating to {'Google Form' if is_google_form else 'page'}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            
            # Wait for content to load
            if is_google_form:
                print("⏳ Waiting for Google Form to fully load...")
                try:
                    # Wait for form content to appear
                    await page.wait_for_selector('[role="list"], .freebirdFormviewerViewItemsItemItem, [jsname]', timeout=20000)
                    await asyncio.sleep(4)  # Extra time for dynamic content
                    
                    # Scroll to load all lazy content
                    await page.evaluate("""
                        async () => {
                            await new Promise((resolve) => {
                                let totalHeight = 0;
                                const distance = 200;
                                const timer = setInterval(() => {
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    
                                    if(totalHeight >= document.body.scrollHeight){
                                        clearInterval(timer);
                                        window.scrollTo(0, 0);
                                        setTimeout(resolve, 1000);
                                    }
                                }, 100);
                            });
                        }
                    """)
                except TimeoutError:
                    print("⚠️ Timeout waiting for form elements, proceeding anyway...")
            else:
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except (TimeoutError, Exception) as e:
                    print(f"⚠️ Network idle timeout ({type(e).__name__}), proceeding...")
                await asyncio.sleep(2)
            
            print("✓ Page loaded, extracting forms...")

            # Use specialized extraction for Google Forms
            if is_google_form:
                forms_data = await _extract_google_forms(page)
            else:
                forms_data = await _extract_standard_forms(page)
            
            print(f"✓ Found {len(forms_data)} form(s)")
            
            # Clean up routes before closing
            try:
                await page.unroute_all(behavior='ignoreErrors')
            except:
                pass
            
            await browser.close()
            
            # Process extracted forms
            for form_data in forms_data:
                form_info = {
                    "formIndex": form_data.get("formIndex"),
                    "action": form_data.get("action"),
                    "method": form_data.get("method", "POST"),
                    "id": form_data.get("id"),
                    "name": form_data.get("name"),
                    "enctype": form_data.get("enctype"),
                    "title": form_data.get("title"),
                    "description": form_data.get("description"),
                    "fields": []
                }
                
                for field_data in form_data.get("fields", []):
                    field_name = field_data.get("name")
                    field_label = field_data.get("label")
                    field_type = field_data.get("type", "text")
                    
                    display_name = _generate_display_name(field_name, field_label, field_data)
                    field_purpose = _detect_field_purpose(field_name, field_label, field_data)
                    
                    field_info = {
                        "name": field_name,
                        "type": field_type,
                        "tagName": field_data.get("tagName"),
                        "label": field_label,
                        "display_name": display_name,
                        "description": field_data.get("description"),
                        "placeholder": field_data.get("placeholder"),
                        "value": field_data.get("value"),
                        "defaultValue": field_data.get("defaultValue"),
                        "validation": field_data.get("validation", {}),
                        "required": field_data.get("required", False),
                        "hidden": field_data.get("hidden", False),
                        "disabled": field_data.get("disabled", False),
                        "readonly": field_data.get("readonly", False),
                        "autocomplete": field_data.get("autocomplete"),
                        "inputmode": field_data.get("inputmode"),
                        "classList": field_data.get("classList", []),
                        "purpose": field_purpose,
                        "is_checkbox": field_type in ["checkbox", "checkbox-group"],
                        "is_multiple_choice": field_type in ["radio", "radio-group", "mcq"],
                        "is_multiple_answer": field_type in ["checkbox-group", "multiple-select"],
                        "is_dropdown": field_type in ["select", "dropdown"],
                        "allows_multiple": field_data.get("allows_multiple", False),
                        "checked": field_data.get("checked")
                    }
                    
                    # Add options for select, radio, checkbox groups
                    if "options" in field_data:
                        field_info["options"] = field_data["options"]
                    
                    # Add file-specific info
                    if field_type == "file":
                        field_info["accept"] = field_data.get("accept")
                        field_info["multiple"] = field_data.get("multiple", False)
                    
                    # Add scale/grid specific info
                    if field_type in ["scale", "grid"]:
                        field_info["scale_min"] = field_data.get("scale_min")
                        field_info["scale_max"] = field_data.get("scale_max")
                        field_info["rows"] = field_data.get("rows")
                        field_info["columns"] = field_data.get("columns")
                    
                    form_info["fields"].append(field_info)
                
                fields.append(form_info)
            
            result = {
                'forms': fields,
                'url': url,
                'is_google_form': is_google_form,
                'total_forms': len(fields),
                'total_fields': sum(len(form['fields']) for form in fields)
            }
            
            # Generate speech for form fields if requested
            if generate_speech and fields:
                try:
                    import os
                    speech_service = SpeechService(api_key=os.getenv('ELEVENLABS_API_KEY'))
                    speech_data = speech_service.generate_form_speech(fields)
                    result['speech'] = speech_data
                except Exception as e:
                    print(f"⚠️ Speech generation failed: {e}")
                    result['speech'] = {}
            
            return result

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return {'forms': [], 'url': url, 'error': str(e)}


async def _extract_google_forms(page) -> List[Dict[str, Any]]:
    """
    Specialized extraction for Google Forms with COMPREHENSIVE support for all question types
    """
    print("🔍 Detected Google Form - using specialized extraction")
    
    # First, let's see what we have on the page
    page_content = await page.content()
    print(f"📄 Page content length: {len(page_content)}")
    
    forms_data = await page.evaluate("""
        () => {
            console.log('Starting Google Forms extraction...');
            
            const forms = [];
            
            // Helper to get visible text
            const getText = (element, selector) => {
                if (!element) return '';
                const el = selector ? element.querySelector(selector) : element;
                if (!el) return '';
                const text = (el.innerText || el.textContent || '').trim();
                return text;
            };
            
            // Helper to get all text from element, including nested
            const getAllText = (element) => {
                if (!element) return '';
                return element.innerText || element.textContent || '';
            };
            
            // Get form title and description with multiple strategies
            let formTitle = '';
            let formDescription = '';
            
            const titleSelectors = [
                '[role="heading"]',
                '.freebirdFormviewerViewHeaderTitle',
                'h1',
                '[jsname="r4nke"]',
                '.M7eMe.lN6iy',
                'div[data-title]'
            ];
            
            for (const sel of titleSelectors) {
                const el = document.querySelector(sel);
                if (el && getText(el)) {
                    formTitle = getText(el);
                    console.log('Found title:', formTitle);
                    break;
                }
            }
            
            const descSelectors = [
                '.freebirdFormviewerViewHeaderDescription',
                '.freebirdFormviewerViewHeaderSubtitle',
                '[jsname="dJNh8b"]',
                '.M7eMe.AgroKb'
            ];
            
            for (const sel of descSelectors) {
                const el = document.querySelector(sel);
                if (el && getText(el)) {
                    formDescription = getText(el);
                    break;
                }
            }
            
            const formInfo = {
                formIndex: 0,
                action: window.location.href,
                method: 'POST',
                id: 'google-form',
                name: formTitle || 'Untitled Form',
                title: formTitle,
                description: formDescription,
                fields: []
            };
            
            // Find all question containers with MULTIPLE strategies
            let questions = [];
            
            const questionSelectors = [
                '[role="listitem"]',  // Most common
                '.freebirdFormviewerViewItemsItemItem',
                '[jsname="ibnC6b"]',  // New Google Forms
                '[data-params*="entry"]',
                '.Qr7Oae',
                '[jsmodel]',
                'div[jscontroller][jsname]'
            ];
            
            for (const selector of questionSelectors) {
                const elements = document.querySelectorAll(selector);
                console.log(`Selector "${selector}" found ${elements.length} elements`);
                
                // Filter to only actual question containers
                const filtered = Array.from(elements).filter(el => {
                    // Must contain input elements OR be a question container
                    const hasInput = el.querySelector('input, select, textarea, [role="radio"], [role="checkbox"], [role="listbox"]');
                    const hasQuestionText = getText(el).length > 0;
                    return hasInput || hasQuestionText;
                });
                
                console.log(`After filtering: ${filtered.length} question elements`);
                
                if (filtered.length > questions.length) {
                    questions = filtered;
                }
            }
            
            console.log(`Processing ${questions.length} questions`);
            
            questions.forEach((question, index) => {
                try {
                    console.log(`\\n=== Processing Question ${index + 1} ===`);
                    
                    // Get question text/label with MULTIPLE strategies
                    let label = '';
                    
                    const labelSelectors = [
                        '[role="heading"]',
                        '.freebirdFormviewerComponentsQuestionBaseTitle',
                        '.M7eMe',
                        '.geS5n',
                        '[jsname="wSASue"]',
                        '[jsname="r4nke"]',
                        'div[dir="auto"]',
                        'span[dir="auto"]'
                    ];
                    
                    for (const sel of labelSelectors) {
                        const el = question.querySelector(sel);
                        if (el) {
                            const text = getText(el);
                            // Filter out empty or very short text
                            if (text && text.length > 2 && !text.match(/^[0-9]+$/)) {
                                label = text;
                                console.log('Found label:', label.substring(0, 50));
                                break;
                            }
                        }
                    }
                    
                    // Fallback: get first significant text
                    if (!label) {
                        const allDivs = question.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.textContent?.trim() || '';
                            if (text.length > 10 && text.length < 500) {
                                label = text;
                                console.log('Fallback label:', label.substring(0, 50));
                                break;
                            }
                        }
                    }
                    
                    if (!label) {
                        console.log('⚠️ No label found for question', index);
                        label = `Question ${index + 1}`;
                    }
                    
                    // Get question description
                    const descSelectors = [
                        '.freebirdFormviewerComponentsQuestionBaseDescription',
                        '.nWQGrd',
                        '[jsname="dJNh8b"]',
                        '.AgroKb'
                    ];
                    let description = '';
                    for (const sel of descSelectors) {
                        const el = question.querySelector(sel);
                        if (el && getText(el)) {
                            description = getText(el);
                            break;
                        }
                    }
                    
                    // Check if required with MULTIPLE strategies
                    const required = 
                        question.querySelector('[aria-label*="Required"]') !== null ||
                        question.querySelector('[aria-label*="required"]') !== null ||
                        question.innerHTML.includes('Required question') ||
                        question.innerHTML.includes('required') ||
                        question.querySelector('.freebirdFormviewerComponentsQuestionBaseRequiredAsterisk') !== null ||
                        question.querySelector('span[aria-label="Required question"]') !== null;
                    
                    console.log('Required:', required);
                    
                    // ===== DETECTION LOGIC =====
                    
                    // 1. SHORT ANSWER / PARAGRAPH
                    const textInput = question.querySelector('input[type="text"]:not([role])') || 
                                    question.querySelector('textarea');
                    if (textInput) {
                        const isTextarea = textInput.tagName === 'TEXTAREA';
                        const name = textInput.name || 
                                   textInput.getAttribute('data-params')?.match(/entry\\.(\\d+)/)?.[1] || 
                                   textInput.getAttribute('jsname') ||
                                   textInput.getAttribute('aria-label') || 
                                   `text_${index}`;
                        
                        console.log(`Found ${isTextarea ? 'PARAGRAPH' : 'SHORT ANSWER'} field:`, name);
                        
                        formInfo.fields.push({
                            name: name,
                            type: isTextarea ? 'textarea' : 'text',
                            tagName: textInput.tagName.toLowerCase(),
                            label: label,
                            description: description,
                            placeholder: textInput.placeholder || null,
                            required: required,
                            hidden: false,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 2. DROPDOWN (Custom Google Forms dropdown)
                    // Check for custom dropdown FIRST before radio buttons
                    const dropdownIndicators = [
                        question.querySelector('[role="listbox"]'),
                        question.querySelector('[role="presentation"] > div[role="option"]'),
                        question.querySelector('div[jsname="LgbsSe"]'),  // Dropdown container
                        question.querySelector('[data-value]'),
                        question.querySelector('.quantumWizMenuPaperselectOption')
                    ];
                    
                    const hasDropdown = dropdownIndicators.some(el => el !== null);
                    const dropdownTrigger = question.querySelector('[role="button"][aria-haspopup="listbox"]') ||
                                          question.querySelector('[aria-expanded]');
                    
                    if (hasDropdown || dropdownTrigger) {
                        console.log('Found DROPDOWN field');
                        const name = question.querySelector('input[type="hidden"]')?.name || `dropdown_${index}`;
                        const options = [];
                        
                        // Try to get options from DOM
                        const optionSelectors = [
                            '[role="option"]',
                            '[data-value]',
                            '.quantumWizMenuPaperselectOption',
                            '.exportOption'
                        ];
                        
                        for (const sel of optionSelectors) {
                            const optionElements = question.querySelectorAll(sel);
                            console.log(`Found ${optionElements.length} options with selector ${sel}`);
                            
                            optionElements.forEach(opt => {
                                const optionText = getText(opt);
                                const optionValue = opt.getAttribute('data-value') || optionText;
                                
                                if (optionText && optionText !== 'Choose' && optionText.length > 0) {
                                    options.push({
                                        value: optionValue,
                                        label: optionText,
                                        selected: opt.getAttribute('aria-selected') === 'true'
                                    });
                                }
                            });
                            
                            if (options.length > 0) break;
                        }
                        
                        // If still no options, look in the entire document (dropdown might be rendered elsewhere)
                        if (options.length === 0) {
                            console.log('Searching for dropdown options in document...');
                            const globalOptions = document.querySelectorAll('[role="option"], .exportOption');
                            globalOptions.forEach(opt => {
                                const optionText = getText(opt);
                                if (optionText && optionText !== 'Choose') {
                                    options.push({
                                        value: optionText,
                                        label: optionText,
                                        selected: false
                                    });
                                }
                            });
                        }
                        
                        console.log(`Extracted ${options.length} dropdown options`);
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'dropdown',
                            tagName: 'custom-select',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            options: options,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 3. STANDARD SELECT DROPDOWN
                    const selectElement = question.querySelector('select');
                    if (selectElement) {
                        console.log('Found SELECT dropdown');
                        const name = selectElement.name || `select_${index}`;
                        const options = [];
                        
                        selectElement.querySelectorAll('option').forEach(opt => {
                            if (opt.value) {
                                options.push({
                                    value: opt.value,
                                    label: opt.text.trim(),
                                    selected: opt.selected,
                                    disabled: opt.disabled
                                });
                            }
                        });
                        
                        console.log(`Extracted ${options.length} select options`);
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'select',
                            tagName: 'select',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            options: options,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 4. MULTIPLE CHOICE (Radio buttons) - Check AFTER dropdown
                    const radioInputs = question.querySelectorAll('input[type="radio"]');
                    const radioRoles = question.querySelectorAll('[role="radio"]');
                    
                    if (radioInputs.length > 0 || radioRoles.length > 0) {
                        console.log(`Found MULTIPLE CHOICE with ${radioInputs.length || radioRoles.length} options`);
                        const name = radioInputs[0]?.name || `mcq_${index}`;
                        const options = [];
                        
                        // Try regular radio inputs first
                        if (radioInputs.length > 0) {
                            radioInputs.forEach(radio => {
                                let optionLabel = radio.getAttribute('aria-label') ||
                                                radio.getAttribute('data-value') ||
                                                radio.value;
                                
                                // Try to get label from parent/sibling
                                if (!optionLabel || optionLabel === 'on') {
                                    const parent = radio.closest('[role="radio"]') || radio.closest('label') || radio.closest('div');
                                    if (parent) {
                                        optionLabel = getText(parent) || radio.value;
                                    }
                                }
                                
                                if (optionLabel && optionLabel.length > 0) {
                                    options.push({
                                        value: radio.value || optionLabel,
                                        label: optionLabel.trim(),
                                        checked: radio.checked
                                    });
                                }
                            });
                        }
                        
                        // Try role="radio" elements
                        if (options.length === 0 && radioRoles.length > 0) {
                            radioRoles.forEach((radio, i) => {
                                const optionText = getText(radio);
                                const dataValue = radio.getAttribute('data-value');
                                
                                if (optionText || dataValue) {
                                    options.push({
                                        value: dataValue || optionText || `option_${i}`,
                                        label: optionText || dataValue || `Option ${i + 1}`,
                                        checked: radio.getAttribute('aria-checked') === 'true'
                                    });
                                }
                            });
                        }
                        
                        console.log(`Extracted ${options.length} radio options`);
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'radio',
                            tagName: 'radio-group',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            options: options,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 5. CHECKBOXES (Multiple answers)
                    const checkboxInputs = question.querySelectorAll('input[type="checkbox"]');
                    const checkboxRoles = question.querySelectorAll('[role="checkbox"]');
                    
                    if (checkboxInputs.length > 0 || checkboxRoles.length > 0) {
                        console.log(`Found CHECKBOX GROUP with ${checkboxInputs.length || checkboxRoles.length} options`);
                        const name = checkboxInputs[0]?.name || `checkbox_${index}`;
                        const options = [];
                        
                        if (checkboxInputs.length > 0) {
                            checkboxInputs.forEach(checkbox => {
                                let optionLabel = checkbox.getAttribute('aria-label') ||
                                                checkbox.getAttribute('data-value') ||
                                                checkbox.value;
                                
                                if (!optionLabel || optionLabel === 'on') {
                                    const parent = checkbox.closest('[role="checkbox"]') || checkbox.closest('label') || checkbox.closest('div');
                                    if (parent) {
                                        optionLabel = getText(parent) || checkbox.value;
                                    }
                                }
                                
                                if (optionLabel && optionLabel.length > 0) {
                                    options.push({
                                        value: checkbox.value || optionLabel,
                                        label: optionLabel.trim(),
                                        checked: checkbox.checked
                                    });
                                }
                            });
                        }
                        
                        if (options.length === 0 && checkboxRoles.length > 0) {
                            checkboxRoles.forEach((checkbox, i) => {
                                const optionText = getText(checkbox);
                                const dataValue = checkbox.getAttribute('data-value');
                                
                                if (optionText || dataValue) {
                                    options.push({
                                        value: dataValue || optionText || `option_${i}`,
                                        label: optionText || dataValue || `Option ${i + 1}`,
                                        checked: checkbox.getAttribute('aria-checked') === 'true'
                                    });
                                }
                            });
                        }
                        
                        console.log(`Extracted ${options.length} checkbox options`);
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'checkbox-group',
                            tagName: 'checkbox-group',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            allows_multiple: true,
                            options: options,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 6. DATE / TIME
                    const dateInput = question.querySelector('input[type="date"]') ||
                                     question.querySelector('input[type="time"]') ||
                                     question.querySelector('input[type="datetime-local"]');
                    if (dateInput) {
                        console.log(`Found ${dateInput.type.toUpperCase()} field`);
                        const name = dateInput.name || `date_${index}`;
                        
                        formInfo.fields.push({
                            name: name,
                            type: dateInput.type,
                            tagName: 'input',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 7. FILE UPLOAD
                    const fileInput = question.querySelector('input[type="file"]');
                    if (fileInput) {
                        console.log('Found FILE UPLOAD field');
                        const name = fileInput.name || `file_${index}`;
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'file',
                            tagName: 'input',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            accept: fileInput.accept || null,
                            multiple: fileInput.multiple,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 8. LINEAR SCALE
                    const scaleContainer = question.querySelector('[role="radiogroup"]');
                    if (scaleContainer) {
                        const scaleRadios = scaleContainer.querySelectorAll('input[type="radio"]');
                        if (scaleRadios.length > 0) {
                            const values = Array.from(scaleRadios).map(r => r.value).filter(v => v);
                            const isNumericScale = values.every(v => !isNaN(v));
                            
                            if (isNumericScale && values.length > 2) {
                                console.log('Found LINEAR SCALE field');
                                const numValues = values.map(v => parseInt(v));
                                const name = scaleRadios[0].name || `scale_${index}`;
                                
                                formInfo.fields.push({
                                    name: name,
                                    type: 'scale',
                                    tagName: 'scale',
                                    label: label,
                                    description: description,
                                    required: required,
                                    hidden: false,
                                    scale_min: Math.min(...numValues),
                                    scale_max: Math.max(...numValues),
                                    options: values.map(v => ({
                                        value: v,
                                        label: v
                                    })),
                                    validation: { required: required }
                                });
                                return;
                            }
                        }
                    }
                    
                    // 9. MULTIPLE CHOICE GRID / CHECKBOX GRID
                    const gridRows = question.querySelectorAll('[role="group"] [role="radiogroup"], [role="group"] [role="group"]');
                    if (gridRows.length > 1) {
                        console.log('Found GRID field');
                        const name = `grid_${index}`;
                        const rows = [];
                        const columns = [];
                        
                        // Extract column headers
                        const columnHeaders = question.querySelectorAll('[role="columnheader"]');
                        columnHeaders.forEach(header => {
                            const colText = getText(header);
                            if (colText) columns.push(colText);
                        });
                        
                        // Extract row labels
                        gridRows.forEach(row => {
                            const rowLabel = getText(row.querySelector('[role="rowheader"]') || 
                                                    row.querySelector('.freebirdFormviewerComponentsQuestionGridRowHeader'));
                            if (rowLabel) rows.push(rowLabel);
                        });
                        
                        console.log(`Grid: ${rows.length} rows, ${columns.length} columns`);
                        
                        formInfo.fields.push({
                            name: name,
                            type: 'grid',
                            tagName: 'grid',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            rows: rows,
                            columns: columns,
                            validation: { required: required }
                        });
                        return;
                    }
                    
                    // 10. Fallback for unidentified fields with label
                    if (label) {
                        console.log('Creating FALLBACK text field for:', label.substring(0, 30));
                        formInfo.fields.push({
                            name: `field_${index}`,
                            type: 'text',
                            tagName: 'input',
                            label: label,
                            description: description,
                            required: required,
                            hidden: false,
                            validation: { required: required }
                        });
                    }
                    
                } catch (e) {
                    console.error(`Error processing question ${index}:`, e);
                }
            });
            
            console.log(`\\n✓ Extracted ${formInfo.fields.length} fields from Google Form`);
            
            return formInfo.fields.length > 0 ? [formInfo] : [];
        }
    """)
    
    return forms_data


async def _extract_standard_forms(page) -> List[Dict[str, Any]]:
    """
    Standard form extraction with enhanced dropdown support
    """
    forms_data = await page.evaluate("""
        () => {
            const forms = [];
            
            const getVisibleText = (element) => {
                if (!element) return '';
                const text = element.innerText || element.textContent || '';
                return text.trim();
            };
            
            const isVisible = (element) => {
                if (!element) return false;
                const style = window.getComputedStyle(element);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0' &&
                       element.offsetParent !== null;
            };
            
            const findLabel = (field, form) => {
                let label = null;
                
                if (field.id) {
                    const labelEl = form.querySelector(`label[for="${field.id}"]`);
                    if (labelEl) label = getVisibleText(labelEl);
                }
                
                if (!label && field.closest('label')) {
                    const parentLabel = field.closest('label');
                    const clone = parentLabel.cloneNode(true);
                    const inputs = clone.querySelectorAll('input, select, textarea');
                    inputs.forEach(i => i.remove());
                    label = getVisibleText(clone);
                }
                
                if (!label) {
                    let sibling = field.previousElementSibling;
                    let attempts = 0;
                    while (sibling && attempts < 3) {
                        if (sibling.tagName === 'LABEL') {
                            label = getVisibleText(sibling);
                            break;
                        }
                        sibling = sibling.previousElementSibling;
                        attempts++;
                    }
                }
                
                if (!label) {
                    let sibling = field.nextElementSibling;
                    if (sibling && sibling.tagName === 'LABEL') {
                        label = getVisibleText(sibling);
                    }
                }
                
                if (!label) {
                    const parent = field.closest('div, li, td, th, fieldset, .form-group, .field');
                    if (parent) {
                        const labelInParent = parent.querySelector('label');
                        if (labelInParent) label = getVisibleText(labelInParent);
                        
                        if (!label) {
                            const legend = parent.querySelector('legend');
                            if (legend) label = getVisibleText(legend);
                        }
                        
                        // Check for heading or strong text
                        if (!label) {
                            const heading = parent.querySelector('h1, h2, h3, h4, h5, h6, strong, b');
                            if (heading) label = getVisibleText(heading);
                        }
                    }
                }
                
                if (!label) {
                    label = field.getAttribute('aria-label') || 
                           (field.getAttribute('aria-labelledby') && 
                            document.getElementById(field.getAttribute('aria-labelledby'))?.innerText);
                }
                
                if (!label) {
                    label = field.getAttribute('title') || field.getAttribute('placeholder');
                }
                
                return label;
            };
            
            const getValidation = (field) => {
                return {
                    required: field.required || field.hasAttribute('required') || field.getAttribute('aria-required') === 'true',
                    pattern: field.getAttribute('pattern') || null,
                    minLength: field.getAttribute('minlength') || field.minLength || null,
                    maxLength: field.getAttribute('maxlength') || field.maxLength || null,
                    min: field.getAttribute('min') || field.min || null,
                    max: field.getAttribute('max') || field.max || null,
                    step: field.getAttribute('step') || field.step || null
                };
            };
            
            // Process each form
            document.querySelectorAll('form').forEach((form, formIndex) => {
                const formInfo = {
                    formIndex: formIndex,
                    action: form.action || window.location.href,
                    method: (form.method || 'GET').toUpperCase(),
                    id: form.id || null,
                    name: form.name || null,
                    enctype: form.enctype || null,
                    fields: []
                };
                
                const seenFields = new Map();
                const fieldSelector = 'input:not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="image"]), select, textarea';
                
                form.querySelectorAll(fieldSelector).forEach((field, fieldIndex) => {
                    if (field.type !== 'hidden' && !isVisible(field)) return;
                    
                    const fieldName = field.name || field.id || `unnamed_${field.tagName}_${fieldIndex}`;
                    
                    if (seenFields.has(fieldName) && field.type !== 'radio' && field.type !== 'checkbox') {
                        return;
                    }
                    
                    const label = findLabel(field, form);
                    const validation = getValidation(field);
                    
                    const fieldInfo = {
                        name: fieldName,
                        type: field.type || field.tagName.toLowerCase(),
                        tagName: field.tagName.toLowerCase(),
                        label: label,
                        placeholder: field.placeholder || null,
                        value: field.value || null,
                        defaultValue: field.defaultValue || null,
                        validation: validation,
                        required: validation.required,
                        hidden: field.type === 'hidden',
                        disabled: field.disabled,
                        readonly: field.readOnly,
                        autocomplete: field.getAttribute('autocomplete') || null,
                        inputmode: field.getAttribute('inputmode') || null,
                        classList: Array.from(field.classList)
                    };
                    
                    // Handle SELECT (dropdown) fields - ENHANCED
                    if (field.tagName === 'SELECT') {
                        fieldInfo.multiple = field.multiple;
                        fieldInfo.allows_multiple = field.multiple;
                        fieldInfo.size = field.size;
                        
                        const options = [];
                        let hasOptgroups = false;
                        
                        // Check for optgroups
                        const optgroups = field.querySelectorAll('optgroup');
                        if (optgroups.length > 0) {
                            hasOptgroups = true;
                            optgroups.forEach(group => {
                                const groupLabel = group.label;
                                group.querySelectorAll('option').forEach(opt => {
                                    options.push({
                                        value: opt.value,
                                        label: opt.text.trim(),
                                        selected: opt.selected,
                                        disabled: opt.disabled,
                                        group: groupLabel
                                    });
                                });
                            });
                        }
                        
                        // Regular options (not in optgroups)
                        field.querySelectorAll('option:not(optgroup option)').forEach(opt => {
                            // Skip empty/placeholder options if they have no value
                            if (!opt.value && (opt.text.trim() === '' || opt.text.trim().toLowerCase().includes('select') || opt.text.trim().toLowerCase().includes('choose'))) {
                                return;
                            }
                            
                            options.push({
                                value: opt.value || opt.text.trim(),
                                label: opt.text.trim(),
                                selected: opt.selected,
                                disabled: opt.disabled
                            });
                        });
                        
                        fieldInfo.options = options;
                        fieldInfo.hasOptgroups = hasOptgroups;
                        
                        console.log(`Found SELECT with ${options.length} options`);
                    }
                    
                    // Handle RADIO buttons (MCQ)
                    if (field.type === 'radio') {
                        if (!seenFields.has(fieldName)) {
                            const radioGroup = form.querySelectorAll(`input[type="radio"][name="${fieldName}"]`);
                            fieldInfo.options = Array.from(radioGroup).map(radio => ({
                                value: radio.value,
                                label: findLabel(radio, form) || radio.value,
                                checked: radio.checked,
                                disabled: radio.disabled
                            }));
                            
                            console.log(`Found RADIO group "${fieldName}" with ${fieldInfo.options.length} options`);
                        } else {
                            return;
                        }
                    }
                    
                    // Handle CHECKBOX
                    if (field.type === 'checkbox') {
                        fieldInfo.checked = field.checked;
                        fieldInfo.value = field.value || 'on';
                        
                        // Check if part of a checkbox group (same name, multiple checkboxes)
                        const checkboxGroup = form.querySelectorAll(`input[type="checkbox"][name="${fieldName}"]`);
                        if (checkboxGroup.length > 1 && !seenFields.has(fieldName + '_group')) {
                            fieldInfo.type = 'checkbox-group';
                            fieldInfo.allows_multiple = true;
                            fieldInfo.options = Array.from(checkboxGroup).map(cb => ({
                                value: cb.value || 'on',
                                label: findLabel(cb, form) || cb.value,
                                checked: cb.checked,
                                disabled: cb.disabled
                            }));
                            seenFields.set(fieldName + '_group', true);
                            
                            console.log(`Found CHECKBOX group "${fieldName}" with ${fieldInfo.options.length} options`);
                        }
                    }
                    
                    // Handle FILE input
                    if (field.type === 'file') {
                        fieldInfo.accept = field.getAttribute('accept') || null;
                        fieldInfo.multiple = field.multiple;
                    }
                    
                    // Handle RANGE input
                    if (field.type === 'range') {
                        fieldInfo.scale_min = field.min;
                        fieldInfo.scale_max = field.max;
                        fieldInfo.step = field.step;
                    }
                    
                    seenFields.set(fieldName, true);
                    formInfo.fields.push(fieldInfo);
                });
                
                if (formInfo.fields.length > 0) {
                    forms.push(formInfo);
                }
            });
            
            return forms;
        }
    """)
    
    return forms_data


def _detect_field_purpose(name: str, label: str, field_data: dict) -> str:
    """Detect the purpose/semantic meaning of a field"""
    field_type = field_data.get("type", "text")
    placeholder = field_data.get("placeholder", "")
    autocomplete = field_data.get("autocomplete", "")
    description = field_data.get("description", "")
    
    text_to_check = ' '.join(filter(None, [
        name or '', 
        label or '', 
        placeholder or '',
        autocomplete or '',
        description or ''
    ])).lower()
    
    if field_type in ['email', 'password', 'tel', 'url', 'date', 'number', 'search', 
                      'checkbox-group', 'radio', 'dropdown', 'scale', 'grid']:
        return field_type
    
    patterns = {
        'email': [r'email', r'e-mail', r'@', r'mail'],
        'password': [r'pass', r'pwd', r'password'],
        'name': [r'\bname\b', r'full.?name', r'first.?name', r'last.?name', r'surname'],
        'phone': [r'phone', r'tel', r'mobile', r'cell', r'contact'],
        'address': [r'address', r'street', r'city', r'state', r'zip', r'postal', r'country'],
        'date': [r'date', r'dob', r'birth', r'day', r'month', r'year'],
        'url': [r'url', r'website', r'link', r'https?://'],
        'search': [r'search', r'query', r'find'],
        'number': [r'amount', r'quantity', r'price', r'count', r'age', r'rating']
    }
    
    for purpose, pattern_list in patterns.items():
        if any(re.search(pattern, text_to_check) for pattern in pattern_list):
            return purpose
    
    return 'text'


def _is_email_field(name: str, label: str, placeholder: str, field_type: str) -> bool:
    """Detect if a field is for email input"""
    return _detect_field_purpose(name, label, {
        'type': field_type,
        'placeholder': placeholder
    }) == 'email'


def _generate_display_name(field_name: str, field_label: str, field_data: dict) -> str:
    """Generate a user-friendly display name for the field"""
    if field_label and len(field_label.strip()) > 0:
        cleaned_label = field_label.strip()
        cleaned_label = re.sub(r'[*:]+', '', cleaned_label).strip()
        if len(cleaned_label) > 0:
            return cleaned_label
    
    placeholder = field_data.get("placeholder") if isinstance(field_data, dict) else None
    if placeholder and len(placeholder.strip()) > 0:
        return placeholder.strip()
    
    description = field_data.get("description") if isinstance(field_data, dict) else None
    if description and len(description.strip()) > 0:
        desc_first_line = description.split('\n')[0].strip()
        if len(desc_first_line) > 0 and len(desc_first_line) < 100:
            return desc_first_line
    
    if field_name:
        clean_name = field_name
        
        for prefix in ['pi_', 'field_', 'input_', 'form_', 'data_', 'user_', 'input-', 
                      'entry.', 'question_', 'mcq_', 'checkbox_', 'dropdown_']:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
        
        clean_name = re.sub(r'_\d+$', '', clean_name)
        clean_name = re.sub(r'\[\]$', '', clean_name)
        clean_name = clean_name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
        clean_name = ' '.join(word.capitalize() for word in clean_name.split())
        
        return clean_name if clean_name else field_name
    
    return "Unnamed Field"


def format_email_input(text: str) -> str:
    """Format text for email fields"""
    if not text:
        return text
    return text.lower().replace(' ', '')


def format_field_value(value: str, field_purpose: str, field_type: str = None) -> str:
    """Format value based on field purpose and type"""
    if not value:
        return value
    
    if field_purpose == 'email':
        return format_email_input(value)
    elif field_purpose == 'phone':
        return re.sub(r'[^\d+\s()-]', '', value)
    elif field_purpose == 'number' or field_type in ['number', 'range']:
        return re.sub(r'[^\d.]', '', value)
    
    return value


def create_template(forms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a template dictionary for form filling"""
    template = {"forms": []}
    
    for form in forms:
        form_template = {
            "form_index": form.get("formIndex"),
            "form_name": form.get("name"),
            "fields": {}
        }
        
        for field in form.get("fields", []):
            field_name = field.get("name")
            field_type = field.get("type")
            
            if not field_name:
                continue
            
            field_template = {
                "display_name": field.get("display_name"),
                "type": field_type,
                "required": field.get("required", False)
            }
            
            if field_type == "checkbox":
                field_template["value"] = False
            elif field_type == "checkbox-group":
                field_template["value"] = []
                field_template["options"] = field.get("options", [])
            elif field_type in ["radio", "mcq", "dropdown", "select"]:
                field_template["value"] = None
                field_template["options"] = field.get("options", [])
            elif field_type == "scale":
                field_template["value"] = None
                field_template["scale_min"] = field.get("scale_min")
                field_template["scale_max"] = field.get("scale_max")
            elif field_type == "grid":
                field_template["value"] = {}
                field_template["rows"] = field.get("rows", [])
                field_template["columns"] = field.get("columns", [])
            elif field_type == "file":
                field_template["value"] = None
                field_template["accept"] = field.get("accept")
                field_template["multiple"] = field.get("multiple", False)
            else:
                field_template["value"] = ""
            
            form_template["fields"][field_name] = field_template
        
        template["forms"].append(form_template)
    
    return template


def get_field_speech(field_name: str, speech_data: dict) -> bytes:
    """Get speech audio for a specific field"""
    field_speech = speech_data.get(field_name, {})
    return field_speech.get('audio', b'')


def get_required_fields(forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all required fields"""
    required = []
    for form in forms:
        for field in form.get("fields", []):
            if field.get("required") and not field.get("hidden"):
                required.append({
                    "form_index": form.get("formIndex"),
                    "form_name": form.get("name"),
                    "name": field.get("name"),
                    "display_name": field.get("display_name"),
                    "type": field.get("type"),
                    "purpose": field.get("purpose"),
                    "options": field.get("options", []) if field.get("options") else None
                })
    return required


def get_mcq_fields(forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all multiple choice questions"""
    mcq = []
    for form in forms:
        for field in form.get("fields", []):
            if field.get("type") in ["radio", "mcq"] and not field.get("hidden"):
                mcq.append({
                    "form_index": form.get("formIndex"),
                    "name": field.get("name"),
                    "display_name": field.get("display_name"),
                    "options": field.get("options", [])
                })
    return mcq


def get_multiple_answer_fields(forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all multiple answer fields"""
    multiple = []
    for form in forms:
        for field in form.get("fields", []):
            if field.get("allows_multiple") and not field.get("hidden"):
                multiple.append({
                    "form_index": form.get("formIndex"),
                    "name": field.get("name"),
                    "display_name": field.get("display_name"),
                    "type": field.get("type"),
                    "options": field.get("options", [])
                })
    return multiple


def get_dropdown_fields(forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all dropdown fields"""
    dropdowns = []
    for form in forms:
        for field in form.get("fields", []):
            if field.get("type") in ["select", "dropdown"] and not field.get("hidden"):
                dropdowns.append({
                    "form_index": form.get("formIndex"),
                    "name": field.get("name"),
                    "display_name": field.get("display_name"),
                    "options": field.get("options", []),
                    "allows_multiple": field.get("allows_multiple", False)
                })
    return dropdowns


def validate_field_value(value: Any, field: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate a field value"""
    validation = field.get("validation", {})
    field_type = field.get("type")
    display_name = field.get("display_name", "Field")
    
    if field.get("required"):
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return False, f"{display_name} is required"
    
    if not value:
        return True, None
    
    if field_type == "checkbox-group":
        if not isinstance(value, list):
            return False, f"{display_name} must be a list"
        valid_options = [opt.get("value") for opt in field.get("options", [])]
        for v in value:
            if v not in valid_options:
                return False, f"Invalid option '{v}'"
        return True, None
    
    if field_type in ["radio", "mcq", "dropdown", "select"]:
        valid_options = [opt.get("value") for opt in field.get("options", [])]
        if value not in valid_options:
            return False, f"Invalid option for {display_name}"
        return True, None
    
    if field_type == "scale":
        try:
            num_value = float(value)
            scale_min = field.get("scale_min")
            scale_max = field.get("scale_max")
            if scale_min and num_value < scale_min:
                return False, f"Must be at least {scale_min}"
            if scale_max and num_value > scale_max:
                return False, f"Must be at most {scale_max}"
        except ValueError:
            return False, f"Must be a number"
        return True, None
    
    if field_type == "grid":
        if not isinstance(value, dict):
            return False, f"Must be a dictionary"
        rows = field.get("rows", [])
        columns = field.get("columns", [])
        for row, col in value.items():
            if row not in rows:
                return False, f"Invalid row '{row}'"
            if col not in columns:
                return False, f"Invalid column '{col}'"
        return True, None
    
    if validation.get("pattern"):
        if not re.match(validation["pattern"], str(value)):
            return False, f"Invalid format"
    
    if validation.get("minLength") and len(str(value)) < int(validation["minLength"]):
        return False, f"Must be at least {validation['minLength']} characters"
    
    if validation.get("maxLength") and len(str(value)) > int(validation["maxLength"]):
        return False, f"Must be no more than {validation['maxLength']} characters"
    
    if field.get("purpose") == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(value)):
            return False, f"Invalid email address"
    
    return True, None


def get_form_summary(forms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get a summary of forms"""
    summary = {
        "total_forms": len(forms),
        "total_fields": 0,
        "field_types": {},
        "required_fields": 0,
        "optional_fields": 0,
        "forms": []
    }
    
    for form in forms:
        form_summary = {
            "name": form.get("name") or form.get("title") or f"Form {form.get('formIndex', 0)}",
            "total_fields": len(form.get("fields", [])),
            "required_fields": 0,
            "field_types": {}
        }
        
        for field in form.get("fields", []):
            summary["total_fields"] += 1
            
            field_type = field.get("type", "text")
            summary["field_types"][field_type] = summary["field_types"].get(field_type, 0) + 1
            form_summary["field_types"][field_type] = form_summary["field_types"].get(field_type, 0) + 1
            
            if field.get("required"):
                summary["required_fields"] += 1
                form_summary["required_fields"] += 1
            else:
                summary["optional_fields"] += 1
        
        summary["forms"].append(form_summary)
    
    return summary