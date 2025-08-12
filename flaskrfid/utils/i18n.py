import os
from flask_babel import Babel, gettext, ngettext
from flask import request

def init_babel(app, babel):
    """Initialize Flask-Babel for internationalization"""
    
    # Configure Babel
    app.config['LANGUAGES'] = {
        'en': 'English',
        'de': 'Deutsch'
    }
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    
    @babel.localeselector
    def get_locale():
        # 1. Check URL parameter
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
        
        # 2. Check session
        if hasattr(request, 'session') and 'language' in request.session:
            return request.session['language']
        
        # 3. Check Accept-Language header
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
    
    return babel

# Translation functions
def _(text):
    """Get translated text"""
    return gettext(text)

def _n(singular, plural, num):
    """Get translated text with pluralization"""
    return ngettext(singular, plural, num)

# Translation dictionary for common RFID system messages
TRANSLATIONS = {
    'en': {
        # System Messages
        'welcome': 'Welcome to School Cafeteria',
        'scan_card': 'Please scan your student card',
        'card_scanned': 'Card scanned successfully',
        'user_not_found': 'User not found',
        'access_denied': 'Access denied',
        'system_error': 'System error occurred',
        
        # User Interface
        'student_profile': 'Student Profile',
        'purchase_items': 'Purchase Items',
        'payment_options': 'Payment Options',
        'select_language': 'Select Language',
        
        # Payment Methods
        'pay_now': 'Pay Now',
        'pay_later': 'Pay Later (Monthly)',
        'cash_payment': 'Cash Payment',
        'card_payment': 'Card Payment',
        'add_to_monthly': 'Add to Monthly Bill',
        
        # Purchase Flow
        'add_to_cart': 'Add to Cart',
        'remove_from_cart': 'Remove from Cart',
        'cart_total': 'Cart Total',
        'complete_purchase': 'Complete Purchase',
        'purchase_completed': 'Purchase Completed',
        
        # User Information
        'name': 'Name',
        'class': 'Class',
        'uid': 'Student ID',
        'category': 'Category',
        'last_scan': 'Last Scan',
        'total_scans': 'Total Scans',
        
        # Food Categories
        'main_course': 'Main Course',
        'snacks': 'Snacks',
        'beverages': 'Beverages',
        'desserts': 'Desserts',
        
        # Status
        'available': 'Available',
        'unavailable': 'Unavailable',
        'active': 'Active',
        'inactive': 'Inactive',
        
        # Actions
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'back': 'Back',
        'next': 'Next',
        'finish': 'Finish',
        
        # Reservations
        'todays_reservations': "Today's Reservations",
        'no_reservations': 'No reservations for today',
        'mark_as_served': 'Mark as Served',
        'reservation_served': 'Reservation marked as served',
        
        # Errors
        'insufficient_funds': 'Insufficient funds',
        'payment_failed': 'Payment failed',
        'card_declined': 'Card declined',
        'try_again': 'Please try again',
        
        # Success Messages
        'payment_successful': 'Payment successful',
        'added_to_monthly_bill': 'Added to monthly bill',
        'parent_notified': 'Parent will be notified',
        
        # Time
        'morning': 'Morning',
        'afternoon': 'Afternoon',
        'evening': 'Evening'
    },
    'de': {
        # System Messages
        'welcome': 'Willkommen in der Schulmensa',
        'scan_card': 'Bitte scannen Sie Ihre Schülerkarte',
        'card_scanned': 'Karte erfolgreich gescannt',
        'user_not_found': 'Benutzer nicht gefunden',
        'access_denied': 'Zugriff verweigert',
        'system_error': 'Systemfehler aufgetreten',
        
        # User Interface
        'student_profile': 'Schülerprofil',
        'purchase_items': 'Artikel kaufen',
        'payment_options': 'Zahlungsoptionen',
        'select_language': 'Sprache wählen',
        
        # Payment Methods
        'pay_now': 'Jetzt bezahlen',
        'pay_later': 'Später bezahlen (Monatlich)',
        'cash_payment': 'Barzahlung',
        'card_payment': 'Kartenzahlung',
        'add_to_monthly': 'Zur Monatsrechnung hinzufügen',
        
        # Purchase Flow
        'add_to_cart': 'In den Warenkorb',
        'remove_from_cart': 'Aus Warenkorb entfernen',
        'cart_total': 'Warenkorb Gesamt',
        'complete_purchase': 'Kauf abschließen',
        'purchase_completed': 'Kauf abgeschlossen',
        
        # User Information
        'name': 'Name',
        'class': 'Klasse',
        'uid': 'Schüler-ID',
        'category': 'Kategorie',
        'last_scan': 'Letzter Scan',
        'total_scans': 'Gesamte Scans',
        
        # Food Categories
        'main_course': 'Hauptgericht',
        'snacks': 'Snacks',
        'beverages': 'Getränke',
        'desserts': 'Desserts',
        
        # Status
        'available': 'Verfügbar',
        'unavailable': 'Nicht verfügbar',
        'active': 'Aktiv',
        'inactive': 'Inaktiv',
        
        # Actions
        'confirm': 'Bestätigen',
        'cancel': 'Abbrechen',
        'back': 'Zurück',
        'next': 'Weiter',
        'finish': 'Fertig',
        
        # Reservations
        'todays_reservations': 'Heutige Reservierungen',
        'no_reservations': 'Keine Reservierungen für heute',
        'mark_as_served': 'Als serviert markieren',
        'reservation_served': 'Reservierung als serviert markiert',
        
        # Errors
        'insufficient_funds': 'Unzureichende Mittel',
        'payment_failed': 'Zahlung fehlgeschlagen',
        'card_declined': 'Karte abgelehnt',
        'try_again': 'Bitte versuchen Sie es erneut',
        
        # Success Messages
        'payment_successful': 'Zahlung erfolgreich',
        'added_to_monthly_bill': 'Zur Monatsrechnung hinzugefügt',
        'parent_notified': 'Eltern werden benachrichtigt',
        
        # Time
        'morning': 'Morgen',
        'afternoon': 'Nachmittag',
        'evening': 'Abend'
    }
}

def get_translation(key, language='en'):
    """Get translation for a key in specified language"""
    return TRANSLATIONS.get(language, {}).get(key, key)