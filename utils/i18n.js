const i18next = require('i18next');
const Backend = require('i18next-fs-backend');
const middleware = require('i18next-http-middleware');
const path = require('path');

// Initialize i18next
i18next
  .use(Backend)
  .use(middleware.LanguageDetector)
  .init({
    lng: 'en', // Default language
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    
    backend: {
      loadPath: path.join(__dirname, '../locales/{{lng}}/{{ns}}.json'),
    },
    
    detection: {
      order: ['header', 'querystring', 'cookie'],
      caches: ['cookie'],
    },
    
    interpolation: {
      escapeValue: false,
    },
    
    resources: {
      en: {
        translation: {
          // System Messages
          welcome: 'Welcome to School Cafeteria',
          scanCard: 'Please scan your student card',
          cardScanned: 'Card scanned successfully',
          userNotFound: 'User not found',
          accessDenied: 'Access denied',
          systemError: 'System error occurred',
          
          // User Interface
          studentProfile: 'Student Profile',
          purchaseItems: 'Purchase Items',
          paymentOptions: 'Payment Options',
          selectLanguage: 'Select Language',
          
          // Payment Methods
          payNow: 'Pay Now',
          payLater: 'Pay Later (Monthly)',
          cashPayment: 'Cash Payment',
          cardPayment: 'Card Payment',
          addToMonthly: 'Add to Monthly Bill',
          
          // Purchase Flow
          addToCart: 'Add to Cart',
          removeFromCart: 'Remove from Cart',
          cartTotal: 'Cart Total',
          completePurchase: 'Complete Purchase',
          purchaseCompleted: 'Purchase Completed',
          
          // User Information
          name: 'Name',
          class: 'Class',
          uid: 'Student ID',
          category: 'Category',
          lastScan: 'Last Scan',
          totalScans: 'Total Scans',
          
          // Food Categories
          mainCourse: 'Main Course',
          snacks: 'Snacks',
          beverages: 'Beverages',
          desserts: 'Desserts',
          
          // Status
          available: 'Available',
          unavailable: 'Unavailable',
          active: 'Active',
          inactive: 'Inactive',
          
          // Actions
          confirm: 'Confirm',
          cancel: 'Cancel',
          back: 'Back',
          next: 'Next',
          finish: 'Finish',
          
          // Reservations
          todaysReservations: "Today's Reservations",
          noReservations: 'No reservations for today',
          markAsServed: 'Mark as Served',
          reservationServed: 'Reservation marked as served',
          
          // Errors
          insufficientFunds: 'Insufficient funds',
          paymentFailed: 'Payment failed',
          cardDeclined: 'Card declined',
          tryAgain: 'Please try again',
          
          // Success Messages
          paymentSuccessful: 'Payment successful',
          addedToMonthlyBill: 'Added to monthly bill',
          parentNotified: 'Parent will be notified',
          
          // Time
          morning: 'Morning',
          afternoon: 'Afternoon',
          evening: 'Evening'
        }
      },
      de: {
        translation: {
          // System Messages
          welcome: 'Willkommen in der Schulmensa',
          scanCard: 'Bitte scannen Sie Ihre Schülerkarte',
          cardScanned: 'Karte erfolgreich gescannt',
          userNotFound: 'Benutzer nicht gefunden',
          accessDenied: 'Zugriff verweigert',
          systemError: 'Systemfehler aufgetreten',
          
          // User Interface
          studentProfile: 'Schülerprofil',
          purchaseItems: 'Artikel kaufen',
          paymentOptions: 'Zahlungsoptionen',
          selectLanguage: 'Sprache wählen',
          
          // Payment Methods
          payNow: 'Jetzt bezahlen',
          payLater: 'Später bezahlen (Monatlich)',
          cashPayment: 'Barzahlung',
          cardPayment: 'Kartenzahlung',
          addToMonthly: 'Zur Monatsrechnung hinzufügen',
          
          // Purchase Flow
          addToCart: 'In den Warenkorb',
          removeFromCart: 'Aus Warenkorb entfernen',
          cartTotal: 'Warenkorb Gesamt',
          completePurchase: 'Kauf abschließen',
          purchaseCompleted: 'Kauf abgeschlossen',
          
          // User Information
          name: 'Name',
          class: 'Klasse',
          uid: 'Schüler-ID',
          category: 'Kategorie',
          lastScan: 'Letzter Scan',
          totalScans: 'Gesamte Scans',
          
          // Food Categories
          mainCourse: 'Hauptgericht',
          snacks: 'Snacks',
          beverages: 'Getränke',
          desserts: 'Desserts',
          
          // Status
          available: 'Verfügbar',
          unavailable: 'Nicht verfügbar',
          active: 'Aktiv',
          inactive: 'Inaktiv',
          
          // Actions
          confirm: 'Bestätigen',
          cancel: 'Abbrechen',
          back: 'Zurück',
          next: 'Weiter',
          finish: 'Fertig',
          
          // Reservations
          todaysReservations: 'Heutige Reservierungen',
          noReservations: 'Keine Reservierungen für heute',
          markAsServed: 'Als serviert markieren',
          reservationServed: 'Reservierung als serviert markiert',
          
          // Errors
          insufficientFunds: 'Unzureichende Mittel',
          paymentFailed: 'Zahlung fehlgeschlagen',
          cardDeclined: 'Karte abgelehnt',
          tryAgain: 'Bitte versuchen Sie es erneut',
          
          // Success Messages
          paymentSuccessful: 'Zahlung erfolgreich',
          addedToMonthlyBill: 'Zur Monatsrechnung hinzugefügt',
          parentNotified: 'Eltern werden benachrichtigt',
          
          // Time
          morning: 'Morgen',
          afternoon: 'Nachmittag',
          evening: 'Abend'
        }
      }
    }
  });

module.exports = i18next;