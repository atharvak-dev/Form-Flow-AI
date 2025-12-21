"""
Constants for form parsing - centralized selectors and patterns.
"""

# Advanced anti-detection script to bypass modern bot protection
STEALTH_SCRIPT = """
// 1. Pass the WebDriver check
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 2. Mock Chrome runtime
window.chrome = {
    runtime: {
        PlatformOs: {
            MAC: 'mac',
            WIN: 'win',
            ANDROID: 'android',
            CROS: 'cros',
            LINUX: 'linux',
            OPENBSD: 'openbsd'
        },
        PlatformArch: {
            ARM: 'arm',
            X86_32: 'x86-32',
            X86_64: 'x86-64',
            MIPS: 'mips',
            MIPS64: 'mips64'
        },
        PlatformNaclArch: {
            ARM: 'arm',
            X86_32: 'x86-32',
            X86_64: 'x86-64',
            MIPS: 'mips',
            MIPS64: 'mips64'
        },
        RequestUpdateCheckStatus: {
            THROTTLED: 'throttled',
            NO_UPDATE: 'no_update',
            UPDATE_AVAILABLE: 'update_available'
        },
        OnInstalledReason: {
            INSTALL: 'install',
            UPDATE: 'update',
            CHROME_UPDATE: 'chrome_update',
            SHARED_MODULE_UPDATE: 'shared_module_update'
        },
        OnRestartRequiredReason: {
            APP_UPDATE: 'app_update',
            OS_UPDATE: 'os_update',
            PERIODIC: 'periodic'
        }
    },
    app: {
        isInstalled: false,
        InstallState: {
            DISABLED: 'disabled',
            INSTALLED: 'installed',
            NOT_INSTALLED: 'not_installed'
        },
        RunningState: {
            CANNOT_RUN: 'cannot_run',
            READY_TO_RUN: 'ready_to_run',
            RUNNING: 'running'
        }
    },
    csi: () => {},
    loadTimes: () => {}
};

// 3. Mock Permissions Query
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: 'granted' }) :
    originalQuery(parameters)
);

// 4. Mock Plugins (Standard Chrome Plugins)
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            {
                name: 'PDF Viewer',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format'
            },
            {
                name: 'Chrome PDF Viewer',
                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                description: 'Portable Document Format'
            },
            {
                name: 'Chromium PDF Viewer',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format'
            },
            {
                name: 'Microsoft Edge PDF Viewer',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format'
            },
            {
                name: 'WebKit built-in PDF',
                filename: 'internal-pdf-viewer',
                description: 'Portable Document Format'
            }
        ];
        return plugins;
    }
});

// 5. Mock Languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// 6. WebGL Vendor Spoofing (Hide being headless)
try {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) return 'Google Inc. (NVIDIA)';
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        return getParameter.call(this, parameter);
    };
} catch (e) {}
"""

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage",
    "--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process", "--window-size=1920,1080"
]

# Field type detection keywords (expanded for exotic types)
FIELD_PATTERNS = {
    # Standard types
    'email': ['email', 'e-mail', 'mail', 'correo'],
    'phone': ['phone', 'mobile', 'tel', 'cell', 'contact', 'whatsapp', 'telefono'],
    'password': ['password', 'pwd', 'pass', 'secret'],
    'name': ['name', 'fullname', 'full_name', 'nombre'],
    'first_name': ['first', 'fname', 'given', 'forename'],
    'last_name': ['last', 'lname', 'surname', 'family'],
    'address': ['address', 'street', 'addr', 'direccion', 'location'],
    'city': ['city', 'town', 'ciudad', 'locality'],
    'state': ['state', 'province', 'region', 'estado'],
    'country': ['country', 'nation', 'pais'],
    'zip': ['zip', 'postal', 'pincode', 'postcode', 'codigo'],
    'date': ['date', 'dob', 'birthday', 'birth', 'fecha', 'when'],
    'url': ['url', 'website', 'link', 'homepage', 'web', 'sitio'],
    'message': ['message', 'comment', 'feedback', 'description', 'note', 'query', 'inquiry', 'question'],
    
    # Exotic types
    'time': ['time', 'hour', 'minute', 'schedule', 'appointment', 'hora', 'cuando'],
    'datetime': ['datetime', 'timestamp', 'when', 'schedule'],
    'color': ['color', 'colour', 'hex', 'rgb', 'hue'],
    'range': ['range', 'slider', 'scale', 'rating', 'satisfaction', 'score', 'level'],
    'file': ['file', 'upload', 'attachment', 'document', 'resume', 'cv', 'photo', 'image', 'archivo'],
    'number': ['number', 'quantity', 'amount', 'count', 'age', 'year', 'numero', 'size'],
    'currency': ['price', 'cost', 'amount', 'salary', 'budget', 'payment', 'fee'],
    'company': ['company', 'organization', 'employer', 'business', 'firm', 'empresa'],
    'job_title': ['title', 'position', 'role', 'designation', 'job', 'occupation', 'puesto'],
    'gender': ['gender', 'sex', 'genero'],
    'age': ['age', 'edad', 'years_old'],
    'website': ['website', 'url', 'blog', 'portfolio', 'linkedin', 'github'],
}

# Custom dropdown component selectors
CUSTOM_DROPDOWN_SELECTORS = [
    # Ant Design
    '.ant-select',
    # Material-UI / MUI
    '.MuiSelect-root', '.MuiAutocomplete-root', '[class*="MuiSelect"]',
    # Vuetify (Vue)
    '.v-select', '.v-autocomplete',
    # Element Plus (Vue)
    '.el-select', '.el-autocomplete',
    # React-Select
    '[class*="select__control"]', '[class*="-control"][class*="css-"]',
    # Select2
    '.select2-container', '.select2',
    # Choices.js
    '.choices',
    # Headless UI (React/Vue) - uses data attributes
    '[data-headlessui-state]',
    # Blueprint.js
    '.bp4-select', '.bp5-select',
    # PrimeReact / PrimeFaces
    '.p-dropdown', '.p-autocomplete',
    # Semantic UI
    '.ui.dropdown', '.ui.selection.dropdown',
    # Bootstrap select variants
    '.bootstrap-select', '.dropdown-toggle[data-toggle="dropdown"]',
    # Tailwind / DaisyUI
    '.select', '[class*="dropdown"]',
    # Generic patterns with ARIA roles
    '[role="combobox"]:not(input)', '[role="listbox"]',
    # Generic class patterns
    '[class*="select-wrapper"]', '[class*="dropdown-wrapper"]',
    '[class*="custom-select"]', '[class*="SelectContainer"]',
]

# Dropdown options selectors (for extracting options from portals)
DROPDOWN_OPTION_SELECTORS = [
    # Ant Design
    '.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option-content',
    '.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item',
    # Material-UI / MUI
    '.MuiMenu-paper .MuiMenuItem-root',
    '.MuiAutocomplete-popper .MuiAutocomplete-option',
    '[class*="MuiMenu"] [class*="MuiMenuItem"]',
    # Vuetify
    '.v-menu__content .v-list-item',
    '.v-select-list .v-list-item__title',
    # Element Plus
    '.el-select-dropdown .el-select-dropdown__item',
    '.el-autocomplete-suggestion li',
    # React-Select
    '[class*="menu"] [class*="option"]',
    '[class*="-menu"] [class*="-option"]',
    # Select2
    '.select2-results__option',
    '.select2-dropdown .select2-results li',
    # Choices.js
    '.choices__list--dropdown .choices__item',
    # Blueprint.js
    '.bp4-menu-item', '.bp5-menu-item',
    # PrimeReact / PrimeFaces
    '.p-dropdown-panel .p-dropdown-item',
    '.p-autocomplete-panel .p-autocomplete-item',
    # Semantic UI
    '.ui.active.visible.dropdown .menu .item',
    '.visible.menu.transition .item',
    # Headless UI
    '[data-headlessui-state*="open"] [role="option"]',
    # Generic ARIA-compliant dropdowns
    '[role="listbox"] [role="option"]',
    '[role="menu"] [role="menuitem"]',
    # Generic patterns
    '.dropdown-menu .dropdown-item',
    '[class*="dropdown"][class*="menu"] [class*="item"]',
    '[class*="options"] [class*="option"]',
]

# Captcha detection selectors
CAPTCHA_SELECTORS = [
    # Google reCAPTCHA
    '.g-recaptcha', '[data-sitekey]', '#recaptcha',
    'iframe[src*="recaptcha"]', 'iframe[src*="google.com/recaptcha"]',
    # hCaptcha
    '.h-captcha', 'iframe[src*="hcaptcha"]',
    # Cloudflare Turnstile
    '.cf-turnstile', '[data-cf-turnstile]',
    # Generic
    '[class*="captcha"]', '[id*="captcha"]',
    'iframe[title*="captcha" i]'
]

# Expandable section selectors
EXPANDABLE_SECTION_SELECTORS = [
    # Ant Design
    '.ant-collapse-header:not(.ant-collapse-header-active)',
    '.ant-tabs-tab:not(.ant-tabs-tab-active)',
    # Bootstrap
    '[data-toggle="collapse"]:not(.show)',
    '.accordion-button.collapsed',
    '.nav-link:not(.active)[data-bs-toggle="tab"]',
    # Material-UI
    '.MuiAccordionSummary-root[aria-expanded="false"]',
    '.MuiTab-root:not(.Mui-selected)',
    # Generic patterns
    '[aria-expanded="false"]',
    '.expandable:not(.expanded)',
    '.collapsible-header:not(.active)',
    '.accordion-header:not(.active)',
    '[class*="expand"]:not([class*="expanded"])',
    # Tab patterns
    '[role="tab"][aria-selected="false"]',
    '.tab:not(.active):not(.selected)',
]

# Wizard/Multi-step form selectors
WIZARD_INDICATORS = [
    '[class*="step"]', '[class*="wizard"]', '[role="tablist"]',
    '.ant-steps', '.MuiStepper-root', '.v-stepper',
    '[data-step]', '[aria-label*="step"]'
]

WIZARD_NEXT_BUTTON_SELECTORS = [
    'button:not([disabled])',
    '.ant-btn-primary',
    '[class*="next"]',
    '[data-action="next"]'
]

# Rich text editor selectors
RICH_TEXT_EDITOR_SELECTORS = {
    'tinymce': '.mce-content-body, [id*="tinymce"]',
    'ckeditor': '.cke_editable, .ck-editor__editable',
    'quill': '.ql-editor',
    'draftjs': '[class*="DraftEditor"]',
    'tiptap': '.ProseMirror',
    'froala': '.fr-element',
}

# Date picker selectors
DATE_PICKER_SELECTORS = [
    '.flatpickr-input', '[data-flatpickr]',
    '.react-datepicker-wrapper input',
    '.vdp-datepicker input',
    '.el-date-editor input',
    '.ant-picker-input input',
    '.MuiPickersPopper-root', '.MuiDatePicker-root',
    '[class*="date-picker"]', '[class*="datepicker"]',
    '.daterangepicker', '[data-date-picker]'
]

# Dropzone/file upload selectors
DROPZONE_SELECTORS = [
    '.dropzone', '[class*="dropzone"]',
    '[class*="file-upload"]', '[class*="upload-area"]',
    '[data-dropzone]', '[role="button"][aria-label*="upload"]',
    '.uppy-Dashboard', '.filepond--root',
    '[class*="drag-drop"]', '[ondrop]'
]

# Range slider selectors
RANGE_SLIDER_SELECTORS = [
    '.noUi-target', '.rc-slider', '.slider', '[class*="slider"]',
    '.MuiSlider-root', '.v-slider', '.el-slider'
]

# Autocomplete selectors
AUTOCOMPLETE_SELECTORS = [
    'input[autocomplete="off"][list]',  # HTML5 datalist
    '.autocomplete', '[class*="autocomplete"]',
    '.typeahead', '[class*="typeahead"]',
    '[role="combobox"][aria-autocomplete="list"]',
    '.awesomplete', '.ui-autocomplete-input',
    '.select2-search__field'
]

# Form-like container selectors (for SPAs without <form> tags)
FORM_LIKE_CONTAINER_SELECTORS = [
    '[role="form"]',
    '[data-form]', '[data-testid*="form"]',
    '[class*="form-container"]', '[class*="form-wrapper"]',
    '[class*="contact-form"]', '[class*="signup-form"]', '[class*="login-form"]',
    '[id*="form"]', '[class*="form"]',
]

# Label selectors by priority
LABEL_SELECTORS = [
    'label', '.label', '.form-label', '.control-label', '.input-label',
    '.ant-form-item-label', '.MuiFormLabel-root', '.v-label', '.el-form-item__label'
]

# Field wrapper selectors
FIELD_WRAPPER_SELECTORS = [
    '.form-group', '.form-field', '.field', '.input-group', '.form-item',
    '.ant-form-item', '.MuiFormControl-root', '.v-input', '.el-form-item',
    '[class*="field"]', '[class*="input-wrapper"]', '[class*="form-row"]'
]

# Google Forms specific selectors
GOOGLE_FORM_SELECTORS = {
    'question_container': '.Qr7Oae, [role="listitem"], .freebirdFormviewerViewItemsItemItem',
    'question_text': '.M7eMe, .freebirdFormviewerComponentsQuestionBaseTitle',
    'text_input': 'input.whsOnd, input[type="text"], .quantumWizTextinputPaperinputInput',
    'textarea': 'textarea.KHxj8b, textarea',
    'radio': '[role="radio"], input[type="radio"]',
    'checkbox': '[role="checkbox"], input[type="checkbox"]',
    'dropdown': '[role="listbox"], .MocG8c',
    'date': '[data-date], .fXgTQe, .KNz39c',
    'time': '[data-date]',
}
