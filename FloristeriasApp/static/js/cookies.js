class CookieManager {
    constructor() {
        this.cookieName = 'cvs_cookie_consent';
        this.cookieExpiry = 365; // días
        this.necessaryCookies = ['csrftoken', 'sessionid'];
        this.init();
    }

    init() {
        // Verificar si ya hay una decisión de cookies
        const consent = this.getCookieConsent();
        
        if (!consent) {
            // Esperar 2 segundos antes de mostrar el banner (más discreto)
            setTimeout(() => {
                this.showBanner();
            }, 2000);
        } else {
            this.handleAnalyticsCookies(consent.analytics);
            this.handleMarketingCookies(consent.marketing);
        }

        this.bindEvents();
    }

    showBanner() {
        const banner = document.getElementById('cookiesBanner');
        if (banner) {
            banner.classList.add('show');
        }
    }

    hideBanner() {
        const banner = document.getElementById('cookiesBanner');
        if (banner) {
            banner.classList.remove('show');
        }
    }

    showSettings() {
        const modal = document.getElementById('cookiesModal');
        if (modal) {
            modal.classList.add('show');
            this.loadCurrentSettings();
        }
    }

    hideSettings() {
        const modal = document.getElementById('cookiesModal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    loadCurrentSettings() {
        const consent = this.getCookieConsent();
        
        if (consent) {
            document.getElementById('analyticsCookies').checked = consent.analytics;
            document.getElementById('marketingCookies').checked = consent.marketing;
        } else {
            // Por defecto: necesarias siempre activas, otras desactivadas
            document.getElementById('analyticsCookies').checked = false;
            document.getElementById('marketingCookies').checked = false;
        }
    }

    acceptAll() {
        const consent = {
            necessary: true,
            analytics: true,
            marketing: true,
            timestamp: new Date().toISOString()
        };
        
        this.setCookieConsent(consent);
        this.hideBanner();
        this.handleAnalyticsCookies(true);
        this.handleMarketingCookies(true);
        
        this.showConfirmation('Todas las cookies han sido aceptadas');
    }

    acceptSelected() {
        const analytics = document.getElementById('analyticsCookies').checked;
        const marketing = document.getElementById('marketingCookies').checked;
        
        const consent = {
            necessary: true,
            analytics: analytics,
            marketing: marketing,
            timestamp: new Date().toISOString()
        };
        
        this.setCookieConsent(consent);
        this.hideSettings();
        this.handleAnalyticsCookies(analytics);
        this.handleMarketingCookies(marketing);
        
        this.showConfirmation('Preferencias de cookies guardadas');
    }

    rejectAll() {
        const consent = {
            necessary: true, // Las necesarias siempre se aceptan
            analytics: false,
            marketing: false,
            timestamp: new Date().toISOString()
        };
        
        this.setCookieConsent(consent);
        this.hideBanner();
        this.handleAnalyticsCookies(false);
        this.handleMarketingCookies(false);
        
        this.showConfirmation('Cookies no esenciales rechazadas');
    }

    setCookieConsent(consent) {
        const expiryDate = new Date();
        expiryDate.setDate(expiryDate.getDate() + this.cookieExpiry);
        
        const cookieValue = JSON.stringify(consent);
        document.cookie = `${this.cookieName}=${cookieValue}; expires=${expiryDate.toUTCString()}; path=/; SameSite=Lax`;
    }

    getCookieConsent() {
        const name = this.cookieName + "=";
        const decodedCookie = decodeURIComponent(document.cookie);
        const ca = decodedCookie.split(';');
        
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return JSON.parse(c.substring(name.length, c.length));
            }
        }
        return null;
    }

    handleAnalyticsCookies(accepted) {
        if (accepted) {
            // Inicializar Google Analytics (reemplaza con tu ID)
            this.loadGoogleAnalytics();
        } else {
            // Deshabilitar analytics
            window['ga-disable-GA_MEASUREMENT_ID'] = true;
        }
    }

    handleMarketingCookies(accepted) {
        if (accepted) {
            // Cargar scripts de marketing (Facebook Pixel, etc.)
            this.loadFacebookPixel();
        }
    }

    loadGoogleAnalytics() {
        // Reemplaza 'GA_MEASUREMENT_ID' con tu ID de Google Analytics
        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID';
        document.head.appendChild(script);

        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID', { anonymize_ip: true });
    }

    loadFacebookPixel() {
        // Código del Facebook Pixel (reemplaza con tu ID)
        console.log('Facebook Pixel cargado (simulado)');
    }

    showConfirmation(message) {
        // Podrías implementar un toast de confirmación aquí
        console.log('Cookie confirmation:', message);
        
        // Ejemplo simple de alerta
        if (typeof showToast === 'function') {
            showToast(message, 'success');
        }
        
        // Mostrar un alert temporal en la consola
        console.log('✅ ' + message);
    }

    bindEvents() {
        // Banner buttons
        document.getElementById('acceptCookies')?.addEventListener('click', () => this.acceptAll());
        document.getElementById('settingsCookies')?.addEventListener('click', () => this.showSettings());
        document.getElementById('rejectCookies')?.addEventListener('click', () => this.rejectAll());

        // Modal buttons
        document.getElementById('saveCookieSettings')?.addEventListener('click', () => this.acceptSelected());
        document.getElementById('closeCookieModal')?.addEventListener('click', () => this.hideSettings());

        // Cerrar modal al hacer clic fuera
        document.getElementById('cookiesModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'cookiesModal') {
                this.hideSettings();
            }
        });

        // Cerrar modal con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideSettings();
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.cookieManager = new CookieManager();
});

// Función para que otros scripts verifiquen el consentimiento
function hasCookieConsent(category) {
    const manager = window.cookieManager;
    if (!manager) return false;
    
    const consent = manager.getCookieConsent();
    return consent ? consent[category] : false;
}