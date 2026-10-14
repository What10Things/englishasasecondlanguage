"""Privacy controls: no optional trackers are currently installed."""
from html import escape
# heading, explanation, essential-only, allow-optional, settings
COPY = {
'en': ('Your cookie choices', 'Essential cookies remember your language and privacy choice and keep forms and checkout secure. No optional analytics or advertising cookies are currently used.', 'Essential only', 'Allow optional cookies', 'Cookie settings'),
'fr': ('Vos choix de cookies', 'Les cookies essentiels mémorisent votre langue et votre choix de confidentialité et sécurisent les formulaires et le paiement. Aucun cookie facultatif de mesure d’audience ou de publicité n’est actuellement utilisé.', 'Essentiels uniquement', 'Autoriser les cookies facultatifs', 'Paramètres des cookies'),
'es': ('Tus preferencias de cookies', 'Las cookies esenciales recuerdan tu idioma y tus preferencias de privacidad y protegen los formularios y el pago. Actualmente no se utilizan cookies opcionales de análisis ni de publicidad.', 'Solo esenciales', 'Permitir cookies opcionales', 'Configuración de cookies'),
'pl': ('Twoje ustawienia plików cookie', 'Niezbędne pliki cookie zapamiętują język i ustawienia prywatności oraz zabezpieczają formularze i płatności. Obecnie nie używamy opcjonalnych plików cookie do analityki ani reklam.', 'Tylko niezbędne', 'Zezwól na opcjonalne', 'Ustawienia plików cookie'),
'hi': ('कुकी संबंधी विकल्प', 'ज़रूरी कुकी आपकी भाषा और गोपनीयता का विकल्प याद रखती हैं और फ़ॉर्म तथा भुगतान को सुरक्षित रखती हैं। अभी विश्लेषण या विज्ञापन के लिए वैकल्पिक कुकी का उपयोग नहीं होता।', 'केवल ज़रूरी कुकी', 'वैकल्पिक कुकी की अनुमति दें', 'कुकी सेटिंग'),
'ur': ('کوکیز کے انتخاب', 'ضروری کوکیز آپ کی زبان اور رازداری کا انتخاب یاد رکھتی ہیں اور فارم اور ادائیگی کو محفوظ بناتی ہیں۔ فی الحال تجزیات یا اشتہارات کے لیے اختیاری کوکیز استعمال نہیں ہوتیں۔', 'صرف ضروری کوکیز', 'اختیاری کوکیز کی اجازت دیں', 'کوکی کی ترتیبات'),
'ps': ('د کوکیز انتخابونه', 'اړینې کوکیز ستاسو ژبه او د محرمیت انتخاب یاد ساتي او فورمې او تادیات خوندي کوي. اوس مهال د شننې یا اعلانونو لپاره اختیاري کوکیز نه کارول کېږي.', 'یوازې اړینې کوکیز', 'اختیاري کوکیز ته اجازه ورکړئ', 'د کوکیز تنظیمات'),
'zh-Hans': ('Cookie 选择', '必要 Cookie 用于记住您的语言和隐私选择，并保障表单和付款安全。目前未使用任何可选的分析或广告 Cookie。', '仅必要 Cookie', '允许可选 Cookie', 'Cookie 设置'),
'zh-Hant': ('Cookie 選擇', '必要 Cookie 用於記住您的語言和隱私選擇，並保障表單和付款安全。目前未使用任何選用的分析或廣告 Cookie。', '僅必要 Cookie', '允許選用 Cookie', 'Cookie 設定'),
}

def controls(language, direction):
    title, body, reject, accept, settings = map(escape, COPY[language])
    return (f'<div class="shell privacy-settings"><button type="button" class="text-button" data-privacy-open>{settings}</button></div>'
            f'<section class="privacy-banner" data-privacy-banner hidden lang="{language}" dir="{direction}" aria-labelledby="privacy-title">'
            f'<div><strong id="privacy-title">{title}</strong><p>{body}</p></div>'
            f'<div class="privacy-actions"><button class="button button-secondary" type="button" data-privacy-choice="essential">{reject}</button>'
            f'<button class="button button-secondary" type="button" data-privacy-choice="optional">{accept}</button></div></section>')
