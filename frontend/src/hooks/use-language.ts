import { useState, useEffect } from 'react'

export type Language = 'en' | 'hi'

const TRANSLATIONS = {
  en: {
    shop: 'Shop',
    scanner: 'AI Scanner',
    intelligence: 'Intelligence',
    admin: 'Admin',
    searchPlaceholder: 'Search 600+ products...',
    addToCart: 'Add to Cart',
    quickAdd: 'Quick Add',
    outOfStock: 'Out of Stock',
    inStock: 'In Stock',
    myOrders: 'My Orders',
    myProfile: 'My Profile',
    signOut: 'Sign Out',
    signIn: 'Sign In',
    cart: 'Cart',
    checkout: 'Checkout',
    reviews: 'Reviews',
    specifications: 'Specifications',
    aiInsights: 'AI Insights',
  },
  hi: {
    shop: 'दुकान',
    scanner: 'एआई स्कैनर',
    intelligence: 'विश्लेषण',
    admin: 'एडमिन',
    searchPlaceholder: '600+ उत्पाद खोजें...',
    addToCart: 'कार्ट में जोड़ें',
    quickAdd: 'झटपट जोड़ें',
    outOfStock: 'स्टॉक में नहीं',
    inStock: 'स्टॉक में उपलब्ध',
    myOrders: 'मेरे ऑर्डर',
    myProfile: 'मेरी प्रोफाइल',
    signOut: 'साइन आउट',
    signIn: 'साइन इन',
    cart: 'कार्ट',
    checkout: 'चेकआउट',
    reviews: 'समीक्षाएं',
    specifications: 'विवरण',
    aiInsights: 'एआई सुझाव',
  },
}

export function useLanguage() {
  const [lang, setLang] = useState<Language>(() => {
    return (localStorage.getItem('app_lang') as Language) || 'en'
  })

  useEffect(() => {
    localStorage.setItem('app_lang', lang)
  }, [lang])

  const toggleLanguage = () => {
    setLang(prev => (prev === 'en' ? 'hi' : 'en'))
  }

  const t = (key: keyof typeof TRANSLATIONS.en) => {
    return TRANSLATIONS[lang][key] || TRANSLATIONS.en[key] || key
  }

  return { lang, toggleLanguage, t }
}
