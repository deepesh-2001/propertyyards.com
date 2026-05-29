import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

/* ─── Tour Script — all steps, all languages ─── */
const STEPS = [
  {
    id: 'welcome',
    route: '/',
    en: { title: 'Welcome to PropertyYards', subtitle: "India's most intelligent real estate platform — powered by AI, built for buyers, sellers and brokers." },
    hi: { title: 'PropertyYards में आपका स्वागत है', subtitle: 'भारत का सबसे स्मार्ट रियल एस्टेट प्लेटफ़ॉर्म — AI द्वारा संचालित, खरीदारों, विक्रेताओं और दलालों के लिए बनाया गया।' },
    mr: { title: 'PropertyYards मध्ये आपले स्वागत आहे', subtitle: 'भारतातील सर्वात बुद्धिमान रिअल इस्टेट व्यासपीठ — AI द्वारे समर्थित.' },
    bn: { title: 'PropertyYards-এ স্বাগতম', subtitle: 'ভারতের সবচেয়ে বুদ্ধিমান রিয়েল এস্টেট প্ল্যাটফর্ম — AI দ্বারা চালিত।' },
    ta: { title: 'PropertyYards-க்கு வரவேற்கிறோம்', subtitle: 'இந்தியாவின் மிகவும் புத்திசாலித்தனமான ரியல் எஸ்டேட் தளம் — AI ஆல் இயக்கப்படுகிறது.' },
    te: { title: 'PropertyYards కి స్వాగతం', subtitle: 'భారతదేశంలో అత్యంత తెలివైన రియల్ ఎస్టేట్ వేదిక — AI ద్వారా నడపబడుతోంది.' },
    emoji: '🏠', icon: 'welcome',
  },
  {
    id: 'search',
    route: '/',
    en: { title: 'AI-Powered Search', subtitle: 'Search across 15,000+ RERA-verified properties with smart filters — by city, budget, BHK, property type and more.' },
    hi: { title: 'AI-संचालित खोज', subtitle: '15,000+ RERA-सत्यापित संपत्तियों में स्मार्ट फ़िल्टर के साथ खोजें — शहर, बजट, BHK और प्रकार द्वारा।' },
    mr: { title: 'AI-चालित शोध', subtitle: 'स्मार्ट फिल्टरसह 15,000+ RERA-सत्यापित मालमत्तांमध्ये शोधा.' },
    bn: { title: 'AI-চালিত অনুসন্ধান', subtitle: 'স্মার্ট ফিল্টার সহ 15,000+ RERA-যাচাইকৃত সম্পত্তি জুড়ে অনুসন্ধান করুন।' },
    ta: { title: 'AI-இயக்கப்படும் தேடல்', subtitle: 'ஸ்மார்ட் ஃபில்டர்களுடன் 15,000+ RERA-சரிபார்க்கப்பட்ட சொத்துக்களில் தேடுங்கள்.' },
    te: { title: 'AI-శక్తి చేత అన్వేషణ', subtitle: 'స్మార్ట్ ఫిల్టర్లతో 15,000+ RERA-ధృవీకరించిన ఆస్తులలో వెతకండి.' },
    emoji: '🔍', icon: 'search',
  },
  {
    id: 'ai_tools',
    route: '/ai-tools',
    en: { title: 'AI Tools Suite', subtitle: 'Generate 3D building models, property descriptions, price predictions and SEO content — all powered by Google Gemini and Imagen AI.' },
    hi: { title: 'AI टूल्स सुइट', subtitle: '3D बिल्डिंग मॉडल, प्रॉपर्टी विवरण, मूल्य भविष्यवाणी और SEO कंटेंट बनाएं — Google Gemini और Imagen AI द्वारा।' },
    mr: { title: 'AI टूल्स सुइट', subtitle: '3D बिल्डिंग मॉडेल, प्रॉपर्टी वर्णन, किंमत अंदाज आणि SEO सामग्री तयार करा.' },
    bn: { title: 'AI টুলস স্যুট', subtitle: '3D বিল্ডিং মডেল, প্রপার্টি বিবরণ, মূল্য পূর্বাভাস এবং SEO কন্টেন্ট তৈরি করুন।' },
    ta: { title: 'AI கருவிகள் தொகுப்பு', subtitle: '3D கட்டிட மாதிரிகள், சொத்து விளக்கங்கள், விலை கணிப்புகள் மற்றும் SEO உள்ளடக்கம் உருவாக்குங்கள்.' },
    te: { title: 'AI టూల్స్ సూట్', subtitle: '3D బిల్డింగ్ మోడల్స్, ప్రాపర్టీ వివరణలు, ధర అంచనాలు మరియు SEO కంటెంట్ రూపొందించండి.' },
    emoji: '✨', icon: 'ai',
  },
  {
    id: 'vastu',
    route: '/ai-tools',
    en: { title: 'Vastu Compatibility Checker', subtitle: 'Check Vastu compliance for every room — Main Door, Kitchen, Bedroom and more. Get instant remedies for any defect.' },
    hi: { title: 'वास्तु अनुकूलता जांच', subtitle: 'हर कमरे के लिए वास्तु अनुपालन जांचें — मुख्य द्वार, रसोई, शयनकक्ष और अधिक। किसी भी दोष के लिए तत्काल उपाय पाएं।' },
    mr: { title: 'वास्तु सुसंगतता तपासणी', subtitle: 'प्रत्येक खोलीसाठी वास्तु अनुपालन तपासा — मुख्य दरवाजा, स्वयंपाकघर, बेडरूम आणि अधिक.' },
    bn: { title: 'বাস্তু সামঞ্জস্য পরীক্ষক', subtitle: 'প্রতিটি ঘরের জন্য বাস্তু সম্মতি পরীক্ষা করুন — প্রধান দরজা, রান্নাঘর, বেডরুম এবং আরও।' },
    ta: { title: 'வாஸ்து இணக்கத்தன்மை சரிபார்ப்பு', subtitle: 'ஒவ்வொரு அறைக்கும் வாஸ்து இணக்கத்தன்மையை சரிபார்க்கவும் — பிரதான கதவு, சமையலறை, படுக்கையறை மற்றும் பலவற்றிற்கும்.' },
    te: { title: 'వాస్తు అనుకూలత తనిఖీ', subtitle: 'ప్రతి గదికి వాస్తు సమ్మతిని తనిఖీ చేయండి — ప్రధాన తలుపు, వంటగది, పడకగది మరియు మరిన్నీ.' },
    emoji: '🧿', icon: 'vastu',
  },
  {
    id: 'crm',
    route: '/crm',
    en: { title: 'Built-in CRM', subtitle: 'Manage all your leads with a Kanban pipeline, interaction history and AI-based lead scoring. Never miss a follow-up again.' },
    hi: { title: 'अंतर्निहित CRM', subtitle: 'Kanban पाइपलाइन, इंटरेक्शन इतिहास और AI-आधारित लीड स्कोरिंग के साथ अपने सभी लीड्स प्रबंधित करें।' },
    mr: { title: 'अंगभूत CRM', subtitle: 'Kanban पाइपलाइन, इंटरेक्शन इतिहास आणि AI-आधारित लीड स्कोअरिंगसह सर्व लीड्स व्यवस्थापित करा.' },
    bn: { title: 'বিল্ট-ইন CRM', subtitle: 'Kanban পাইপলাইন, ইন্টারঅ্যাকশন ইতিহাস এবং AI-ভিত্তিক লিড স্কোরিং দিয়ে সমস্ত লিড পরিচালনা করুন।' },
    ta: { title: 'உள்ளமைக்கப்பட்ட CRM', subtitle: 'Kanban பைப்லைன், தொடர்பு வரலாறு மற்றும் AI-அடிப்படையிலான லீட் ஸ்கோரிங் மூலம் அனைத்து லீட்களையும் நிர்வகிக்கவும்.' },
    te: { title: 'అంతర్నిర్మిత CRM', subtitle: 'Kanban పైప్‌లైన్, ఇంటరాక్షన్ చరిత్ర మరియు AI-ఆధారిత లీడ్ స్కోరింగ్‌తో అన్ని లీడ్‌లను నిర్వహించండి.' },
    emoji: '📋', icon: 'crm',
  },
  {
    id: 'analytics',
    route: '/analytics',
    en: { title: 'Real-Time Analytics', subtitle: 'Live price trends, demand heatmaps and locality scores. Track your listings performance and market movements in real time.' },
    hi: { title: 'रियल-टाइम एनालिटिक्स', subtitle: 'लाइव मूल्य प्रवृत्तियां, मांग हीटमैप और लोकेलिटी स्कोर। अपनी लिस्टिंग प्रदर्शन और बाजार की गतिविधियों को ट्रैक करें।' },
    mr: { title: 'रिअल-टाइम एनालिटिक्स', subtitle: 'लाइव किंमत ट्रेंड, मागणी हीटमॅप आणि लोकॅलिटी स्कोअर. आपल्या लिस्टिंगची कामगिरी ट्रॅक करा.' },
    bn: { title: 'রিয়েল-টাইম অ্যানালিটিক্স', subtitle: 'লাইভ মূল্য প্রবণতা, চাহিদা হিটম্যাপ এবং লোকালিটি স্কোর। আপনার লিস্টিং পারফরম্যান্স ট্র্যাক করুন।' },
    ta: { title: 'நிகழ்நேர பகுப்பாய்வு', subtitle: 'நேரடி விலை போக்குகள், தேவை ஹீட்மேப்கள் மற்றும் லோகாலிட்டி ஸ்கோர்கள். உங்கள் பட்டியல் செயல்திறனை கண்காணிக்கவும்.' },
    te: { title: 'రియల్-టైమ్ అనలిటిక్స్', subtitle: 'లైవ్ ధర ట్రెండ్‌లు, డిమాండ్ హీట్‌మ్యాప్‌లు మరియు లొకాలిటీ స్కోర్‌లు. మీ లిస్టింగ్ పనితీరును ట్రాక్ చేయండి.' },
    emoji: '📊', icon: 'analytics',
  },
  {
    id: 'payments',
    route: '/payments',
    en: { title: 'Payments & Wallet', subtitle: 'Manage transactions, pay installments, download invoices and track subscriptions — all from one secure wallet.' },
    hi: { title: 'पेमेंट और वॉलेट', subtitle: 'लेनदेन प्रबंधित करें, किस्तें चुकाएं, चालान डाउनलोड करें और सदस्यता ट्रैक करें — एक सुरक्षित वॉलेट से।' },
    mr: { title: 'पेमेंट आणि वॉलेट', subtitle: 'व्यवहार व्यवस्थापित करा, हप्ते भरा, चालान डाउनलोड करा आणि सदस्यता ट्रॅक करा.' },
    bn: { title: 'পেমেন্ট ও ওয়ালেট', subtitle: 'লেনদেন পরিচালনা করুন, কিস্তি পরিশোধ করুন, চালান ডাউনলোড করুন এবং সাবস্ক্রিপশন ট্র্যাক করুন।' },
    ta: { title: 'பேமெண்ட் மற்றும் வாலட்', subtitle: 'பரிவர்த்தனைகளை நிர்வகிக்கவும், தவணைகளை செலுத்தவும், விலைப்பட்டியல்களை பதிவிறக்கவும்.' },
    te: { title: 'చెల్లింపులు & వాలెట్', subtitle: 'లావాదేవీలను నిర్వహించండి, వాయిదాలు చెల్లించండి, ఇన్‌వాయిస్‌లు డౌన్‌లోడ్ చేయండి.' },
    emoji: '💳', icon: 'payments',
  },
  {
    id: 'rewards',
    route: '/rewards',
    en: { title: 'Rewards & Referrals', subtitle: 'Earn points for every action — inquiries, referrals, listings. Redeem as Amazon gift cards, cashback or wallet credits.' },
    hi: { title: 'रिवॉर्ड्स और रेफरल', subtitle: 'हर कार्य के लिए पॉइंट अर्जित करें — पूछताछ, रेफरल, लिस्टिंग। Amazon गिफ्ट कार्ड, कैशबैक या वॉलेट क्रेडिट के रूप में भुनाएं।' },
    mr: { title: 'रिवॉर्ड्स आणि रेफरल', subtitle: 'प्रत्येक क्रियेसाठी पॉइंट्स मिळवा. Amazon गिफ्ट कार्ड, कॅशबॅक किंवा वॉलेट क्रेडिट म्हणून रिडीम करा.' },
    bn: { title: 'পুরস্কার এবং রেফারেল', subtitle: 'প্রতিটি কাজের জন্য পয়েন্ট অর্জন করুন। Amazon গিফট কার্ড, ক্যাশব্যাক বা ওয়ালেট ক্রেডিট হিসেবে রিডিম করুন।' },
    ta: { title: 'வெகுமதிகள் மற்றும் பரிந்துரைகள்', subtitle: 'ஒவ்வொரு செயலுக்கும் புள்ளிகள் சம்பாதிக்கவும். Amazon கிஃப்ட் கார்டுகள், கேஷ்பேக் அல்லது வாலட் கிரெடிட்டாக மாற்றவும்.' },
    te: { title: 'రివార్డ్‌లు & రిఫెరల్‌లు', subtitle: 'ప్రతి చర్యకు పాయింట్లు సంపాదించండి. Amazon గిఫ్ట్ కార్డ్‌లు, క్యాష్‌బ్యాక్ లేదా వాలెట్ క్రెడిట్‌లుగా రీడీమ్ చేయండి.' },
    emoji: '🎁', icon: 'rewards',
  },
  {
    id: 'notifications',
    route: '/notifications',
    en: { title: 'Notification Center', subtitle: 'Get instant alerts via WhatsApp, email and in-app. Set per-channel preferences for price drops, new matches and inquiry responses.' },
    hi: { title: 'नोटिफिकेशन सेंटर', subtitle: 'WhatsApp, ईमेल और इन-ऐप के माध्यम से तत्काल अलर्ट प्राप्त करें। कीमत में गिरावट, नए मैच और पूछताछ के लिए प्राथमिकताएं सेट करें।' },
    mr: { title: 'नोटिफिकेशन सेंटर', subtitle: 'WhatsApp, ईमेल आणि इन-ऐपद्वारे त्वरित सूचना मिळवा. किंमत घसरण आणि नवीन जुळणीसाठी प्राधान्ये सेट करा.' },
    bn: { title: 'নোটিফিকেশন সেন্টার', subtitle: 'WhatsApp, ইমেইল এবং ইন-অ্যাপের মাধ্যমে তাৎক্ষণিক সতর্কতা পান। দাম কমা এবং নতুন ম্যাচের জন্য পছন্দ সেট করুন।' },
    ta: { title: 'அறிவிப்பு மையம்', subtitle: 'WhatsApp, மின்னஞ்சல் மற்றும் இன்-ஆப் மூலம் உடனடி எச்சரிக்கைகள் பெறுங்கள்.' },
    te: { title: 'నోటిఫికేషన్ సెంటర్', subtitle: 'WhatsApp, ఇమెయిల్ మరియు ఇన్-యాప్ ద్వారా తక్షణ హెచ్చరికలు పొందండి.' },
    emoji: '🔔', icon: 'notifications',
  },
  {
    id: 'social',
    route: '/social-media',
    en: { title: 'Social Media Manager', subtitle: 'Schedule property posts to Instagram, Facebook, LinkedIn and more. Use AI templates and track reach, engagement and leads per platform.' },
    hi: { title: 'सोशल मीडिया मैनेजर', subtitle: 'Instagram, Facebook, LinkedIn पर प्रॉपर्टी पोस्ट शेड्यूल करें। AI टेम्पलेट उपयोग करें और प्रत्येक प्लेटफ़ॉर्म पर पहुंच और जुड़ाव ट्रैक करें।' },
    mr: { title: 'सोशल मीडिया मॅनेजर', subtitle: 'Instagram, Facebook, LinkedIn वर प्रॉपर्टी पोस्ट शेड्यूल करा. AI टेम्पलेट वापरा.' },
    bn: { title: 'সোশ্যাল মিডিয়া ম্যানেজার', subtitle: 'Instagram, Facebook, LinkedIn-এ প্রপার্টি পোস্ট শিডিউল করুন। AI টেমপ্লেট ব্যবহার করুন।' },
    ta: { title: 'சமூக ஊடக மேலாளர்', subtitle: 'Instagram, Facebook, LinkedIn-ல் சொத்து இடுகைகளை திட்டமிடுங்கள். AI வார்ப்புருக்களை பயன்படுத்துங்கள்.' },
    te: { title: 'సోషల్ మీడియా మేనేజర్', subtitle: 'Instagram, Facebook, LinkedIn లో ప్రాపర్టీ పోస్ట్‌లను షెడ్యూల్ చేయండి.' },
    emoji: '📱', icon: 'social',
  },
  {
    id: 'admin',
    route: '/admin',
    en: { title: 'Admin Portal', subtitle: 'Full control over users, listings, feature flags, system health and reports. Built for platform administrators and team managers.' },
    hi: { title: 'एडमिन पोर्टल', subtitle: 'उपयोगकर्ताओं, लिस्टिंग, फीचर फ्लैग, सिस्टम हेल्थ और रिपोर्ट पर पूर्ण नियंत्रण।' },
    mr: { title: 'अॅडमिन पोर्टल', subtitle: 'वापरकर्ते, लिस्टिंग, फीचर फ्लॅग, सिस्टम हेल्थ आणि रिपोर्ट्सवर संपूर्ण नियंत्रण.' },
    bn: { title: 'অ্যাডমিন পোর্টাল', subtitle: 'ব্যবহারকারী, লিস্টিং, ফিচার ফ্ল্যাগ, সিস্টেম স্বাস্থ্য এবং রিপোর্টের উপর সম্পূর্ণ নিয়ন্ত্রণ।' },
    ta: { title: 'நிர்வாக போர்ட்டல்', subtitle: 'பயனர்கள், பட்டியல்கள், அம்சக் கொடிகள், கணினி சுகாதாரம் மற்றும் அறிக்கைகள் மீது முழு கட்டுப்பாடு.' },
    te: { title: 'అడ్మిన్ పోర్టల్', subtitle: 'వినియోగదారులు, లిస్టింగ్‌లు, ఫీచర్ ఫ్లాగ్‌లు, సిస్టమ్ హెల్త్ మరియు రిపోర్ట్‌లపై పూర్తి నియంత్రణ.' },
    emoji: '⚙️', icon: 'admin',
  },
  {
    id: 'finish',
    route: '/',
    en: { title: 'That\'s PropertyYards!', subtitle: 'The complete real estate platform — 20+ features, AI-powered, RERA-verified. Start your free trial today.' },
    hi: { title: 'यही है PropertyYards!', subtitle: 'संपूर्ण रियल एस्टेट प्लेटफ़ॉर्म — 20+ फीचर, AI-संचालित, RERA-सत्यापित। आज अपना मुफ्त ट्रायल शुरू करें।' },
    mr: { title: 'हेच आहे PropertyYards!', subtitle: 'संपूर्ण रिअल इस्टेट व्यासपीठ — 20+ वैशिष्ट्ये, AI-चालित, RERA-सत्यापित. आज आपली विनामूल्य चाचणी सुरू करा.' },
    bn: { title: 'এটাই PropertyYards!', subtitle: 'সম্পূর্ণ রিয়েল এস্টেট প্ল্যাটফর্ম — 20+ ফিচার, AI-চালিত, RERA-যাচাইকৃত। আজই আপনার বিনামূল্যে ট্রায়াল শুরু করুন।' },
    ta: { title: 'இதுவே PropertyYards!', subtitle: 'முழுமையான ரியல் எஸ்டேட் தளம் — 20+ அம்சங்கள், AI-இயக்கப்படுகிறது, RERA-சரிபார்க்கப்பட்டது.' },
    te: { title: 'ఇదే PropertyYards!', subtitle: 'పూర్తి రియల్ ఎస్టేట్ ప్లాట్‌ఫారమ్ — 20+ ఫీచర్లు, AI-శక్తి చేత, RERA-ధృవీకరించబడింది.' },
    emoji: '🎉', icon: 'finish',
  },
]

const LANGUAGES = [
  { code: 'en', label: 'English',    flag: '🇬🇧' },
  { code: 'hi', label: 'हिन्दी',      flag: '🇮🇳' },
  { code: 'mr', label: 'मराठी',       flag: '🇮🇳' },
  { code: 'bn', label: 'বাংলা',       flag: '🇮🇳' },
  { code: 'ta', label: 'தமிழ்',       flag: '🇮🇳' },
  { code: 'te', label: 'తెలుగు',      flag: '🇮🇳' },
]

const ICON_SVG = {
  welcome: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#1a56db22" />
      <path d="M20 8L6 18v14h10v-8h8v8h10V18L20 8z" fill="#1a56db" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#7c3aed22" />
      <circle cx="18" cy="18" r="7" stroke="#7c3aed" strokeWidth="2.5" fill="none" />
      <line x1="23" y1="23" x2="31" y2="31" stroke="#7c3aed" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  ),
  ai: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#f59e0b22" />
      <path d="M20 10l2 6h6l-5 4 2 6-5-4-5 4 2-6-5-4h6z" fill="#f59e0b" />
    </svg>
  ),
  vastu: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#059669" fillOpacity="0.12" />
      <circle cx="20" cy="20" r="10" stroke="#059669" strokeWidth="2" fill="none" />
      <line x1="20" y1="10" x2="20" y2="30" stroke="#059669" strokeWidth="1.5" />
      <line x1="10" y1="20" x2="30" y2="20" stroke="#059669" strokeWidth="1.5" />
      <circle cx="20" cy="20" r="3" fill="#059669" />
    </svg>
  ),
  crm: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#ec489922" />
      <rect x="8" y="12" width="7" height="16" rx="2" fill="#ec4899" />
      <rect x="17" y="8" width="7" height="20" rx="2" fill="#ec4899" opacity="0.7" />
      <rect x="26" y="15" width="7" height="13" rx="2" fill="#ec4899" opacity="0.4" />
    </svg>
  ),
  analytics: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#0284c722" />
      <polyline points="8,30 16,18 22,24 30,10" stroke="#0284c7" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="30" cy="10" r="2.5" fill="#0284c7" />
    </svg>
  ),
  payments: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#05966922" />
      <rect x="6" y="12" width="28" height="18" rx="3" stroke="#059669" strokeWidth="2" fill="none" />
      <line x1="6" y1="18" x2="34" y2="18" stroke="#059669" strokeWidth="2" />
      <rect x="10" y="22" width="8" height="3" rx="1" fill="#059669" />
    </svg>
  ),
  rewards: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#f59e0b22" />
      <path d="M20 8l2.5 7H30l-6 4.5 2.5 7-7-5-7 5 2.5-7L9 15h7.5z" fill="#f59e0b" />
    </svg>
  ),
  notifications: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#1a56db22" />
      <path d="M20 8a9 9 0 00-9 9v6l-2 3h22l-2-3v-6a9 9 0 00-9-9z" stroke="#1a56db" strokeWidth="2" fill="none" />
      <path d="M17 29a3 3 0 006 0" stroke="#1a56db" strokeWidth="2" fill="none" />
    </svg>
  ),
  social: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#E1306C22" />
      <circle cx="20" cy="20" r="7" stroke="#E1306C" strokeWidth="2" fill="none" />
      <circle cx="20" cy="20" r="3" fill="#E1306C" />
      <circle cx="29" cy="11" r="2" fill="#E1306C" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#64748b22" />
      <circle cx="20" cy="20" r="7" stroke="#64748b" strokeWidth="2" fill="none" />
      <circle cx="20" cy="20" r="3" fill="#64748b" />
      <line x1="20" y1="8" x2="20" y2="12" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
      <line x1="20" y1="28" x2="20" y2="32" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
      <line x1="8" y1="20" x2="12" y2="20" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
      <line x1="28" y1="20" x2="32" y2="20" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  finish: (
    <svg viewBox="0 0 40 40" fill="none" style={{ width: 40, height: 40 }}>
      <rect width="40" height="40" rx="12" fill="#7c3aed22" />
      <path d="M12 20l6 6 10-12" stroke="#7c3aed" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  ),
}

/* ── AI Avatar character ── */
function AIAvatar({ speaking, lang }) {
  const [blink, setBlink] = useState(false)
  const [mouth, setMouth] = useState(0)

  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlink(true)
      setTimeout(() => setBlink(false), 120)
    }, 3000 + Math.random() * 2000)
    return () => clearInterval(blinkInterval)
  }, [])

  useEffect(() => {
    if (!speaking) { setMouth(0); return }
    const mouthInterval = setInterval(() => setMouth(m => (m + 1) % 3), 140)
    return () => clearInterval(mouthInterval)
  }, [speaking])

  const eyeH = blink ? 1 : 8

  return (
    <div style={av.wrap}>
      {/* Glow ring */}
      <div style={{ ...av.glowRing, animation: speaking ? 'spin 3s linear infinite' : 'none' }} />
      {/* Avatar body */}
      <div style={av.body}>
        <svg viewBox="0 0 80 80" style={{ width: 80, height: 80 }}>
          {/* Head */}
          <circle cx="40" cy="38" r="26" fill="url(#avatarGrad)" />
          <defs>
            <radialGradient id="avatarGrad" cx="40%" cy="35%">
              <stop offset="0%" stopColor="#60a5fa" />
              <stop offset="100%" stopColor="#1a56db" />
            </radialGradient>
          </defs>
          {/* Eyes */}
          <rect x="28" y={34 - eyeH / 2} width="7" height={eyeH} rx="3.5" fill="#fff" />
          <rect x="45" y={34 - eyeH / 2} width="7" height={eyeH} rx="3.5" fill="#fff" />
          {/* Pupils */}
          {!blink && <>
            <circle cx="31.5" cy="34" r="2" fill="#0f172a" />
            <circle cx="48.5" cy="34" r="2" fill="#0f172a" />
            <circle cx="32.5" cy="33" r="0.7" fill="#fff" />
            <circle cx="49.5" cy="33" r="0.7" fill="#fff" />
          </>}
          {/* Mouth */}
          {mouth === 0 && <path d="M33 45 Q40 50 47 45" stroke="#fff" strokeWidth="2" fill="none" strokeLinecap="round" />}
          {mouth === 1 && <ellipse cx="40" cy="46" rx="5" ry="3" fill="#0f172a" opacity="0.7" />}
          {mouth === 2 && <ellipse cx="40" cy="46" rx="6" ry="4" fill="#0f172a" opacity="0.7" />}
          {/* Antenna */}
          <line x1="40" y1="12" x2="40" y2="18" stroke="#93c5fd" strokeWidth="2" />
          <circle cx="40" cy="10" r="3" fill={speaking ? '#fbbf24' : '#93c5fd'} />
          {speaking && <circle cx="40" cy="10" r="6" fill="#fbbf24" opacity="0.3" />}
          {/* Neck */}
          <rect x="35" y="62" width="10" height="6" rx="2" fill="#1a56db" />
          {/* Shoulders */}
          <rect x="20" y="68" width="40" height="8" rx="4" fill="#1a56db" />
          {/* Badge */}
          <rect x="33" y="70" width="14" height="4" rx="2" fill="#93c5fd" opacity="0.6" />
        </svg>
        {/* Sound waves when speaking */}
        {speaking && (
          <div style={av.waves}>
            {[0, 1, 2].map(i => (
              <div key={i} style={{ ...av.wave, animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        )}
      </div>
      <div style={av.name}>Aria · PropertyYards AI</div>
    </div>
  )
}

/* ── Typewriter subtitle ── */
function Typewriter({ text, speed = 28, onDone }) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone]           = useState(false)
  const idx = useRef(0)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    idx.current = 0
    if (!text) return
    const interval = setInterval(() => {
      idx.current += 1
      setDisplayed(text.slice(0, idx.current))
      if (idx.current >= text.length) {
        clearInterval(interval)
        setDone(true)
        onDone?.()
      }
    }, speed)
    return () => clearInterval(interval)
  }, [text])

  return (
    <span>
      {displayed}
      {!done && <span style={{ borderRight: '2px solid #fff', marginLeft: 1, animation: 'blink 0.7s step-end infinite' }} />}
    </span>
  )
}

/* ── Main DemoTour component ── */
export default function DemoTour() {
  const navigate  = useNavigate()
  const [open, setOpen]         = useState(false)
  const [lang, setLang]         = useState('en')
  const [step, setStep]         = useState(0)
  const [speaking, setSpeaking] = useState(false)
  const [subtitleDone, setSubtitleDone] = useState(false)
  const [paused, setPaused]     = useState(false)
  const [showLangMenu, setShowLangMenu] = useState(false)
  const autoTimer = useRef(null)

  const current = STEPS[step]
  const content = current?.[lang] || current?.en

  const goToStep = useCallback((idx) => {
    if (idx < 0 || idx >= STEPS.length) return
    setStep(idx)
    setSubtitleDone(false)
    setSpeaking(true)
    navigate(STEPS[idx].route)
  }, [navigate])

  const next = useCallback(() => goToStep(step + 1), [step, goToStep])
  const prev = useCallback(() => goToStep(step - 1), [step, goToStep])

  // Auto advance after subtitle finishes + 2s delay
  useEffect(() => {
    if (!open || paused) return
    if (subtitleDone && step < STEPS.length - 1) {
      autoTimer.current = setTimeout(() => next(), 2200)
    }
    return () => clearTimeout(autoTimer.current)
  }, [subtitleDone, open, paused, step, next])

  // Navigate when step changes
  useEffect(() => {
    if (open) navigate(current.route)
  }, [step, open])

  // Speaking animation tied to subtitle
  useEffect(() => {
    if (!open) return
    setSpeaking(true)
    setSubtitleDone(false)
  }, [step, open])

  const launch = () => {
    setStep(0)
    setSubtitleDone(false)
    setSpeaking(true)
    setPaused(false)
    setOpen(true)
    navigate(STEPS[0].route)
  }

  const close = () => {
    setOpen(false)
    clearTimeout(autoTimer.current)
    setSpeaking(false)
  }

  const togglePause = () => {
    setPaused(p => !p)
    clearTimeout(autoTimer.current)
  }

  const progress = ((step) / (STEPS.length - 1)) * 100

  if (!open) {
    return (
      <button onClick={launch} style={s.launchBtn} title="Start Demo Tour">
        <span style={{ fontSize: 22 }}>🤖</span>
        <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.3px' }}>Demo Tour</span>
      </button>
    )
  }

  return (
    <>
      {/* Dim overlay */}
      <div style={s.overlay} onClick={close} />

      {/* Main narrator card */}
      <div style={s.card}>
        {/* Progress bar */}
        <div style={s.progressTrack}>
          <div style={{ ...s.progressFill, width: `${progress}%` }} />
        </div>

        {/* Header */}
        <div style={s.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={s.stepBadge}>{step + 1} / {STEPS.length}</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#64748b' }}>PropertyYards Demo</span>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* Language picker */}
            <div style={{ position: 'relative' }}>
              <button onClick={() => setShowLangMenu(m => !m)} style={s.langBtn}>
                {LANGUAGES.find(l => l.code === lang)?.flag} {LANGUAGES.find(l => l.code === lang)?.label} ▾
              </button>
              {showLangMenu && (
                <div style={s.langMenu}>
                  {LANGUAGES.map(l => (
                    <button key={l.code} onClick={() => { setLang(l.code); setShowLangMenu(false); setSubtitleDone(false) }}
                      style={{ ...s.langOption, ...(lang === l.code ? { background: '#eff6ff', color: '#1a56db', fontWeight: 800 } : {}) }}>
                      {l.flag} {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={close} style={s.closeBtn}>✕</button>
          </div>
        </div>

        {/* Body */}
        <div style={s.body}>
          {/* Avatar */}
          <AIAvatar speaking={speaking && !subtitleDone} lang={lang} />

          {/* Content */}
          <div style={s.content}>
            <div style={s.stepEmoji}>{current.emoji}</div>
            <div style={s.stepTitle}>{content.title}</div>
            <div style={s.subtitleBox}>
              <Typewriter
                key={`${step}-${lang}`}
                text={content.subtitle}
                speed={26}
                onDone={() => { setSubtitleDone(true); setSpeaking(false) }}
              />
            </div>
          </div>
        </div>

        {/* Step dots */}
        <div style={s.dots}>
          {STEPS.map((_, i) => (
            <button key={i} onClick={() => goToStep(i)}
              style={{ ...s.dot, ...(i === step ? s.dotActive : i < step ? s.dotDone : {}) }}
              title={STEPS[i][lang]?.title || STEPS[i].en.title}
            />
          ))}
        </div>

        {/* Controls */}
        <div style={s.controls}>
          <button onClick={prev} disabled={step === 0} style={{ ...s.navBtn, opacity: step === 0 ? 0.3 : 1 }}>← Prev</button>
          <button onClick={togglePause} style={s.pauseBtn}>
            {paused ? '▶ Resume' : '⏸ Pause'}
          </button>
          {step === STEPS.length - 1 ? (
            <button onClick={close} style={{ ...s.navBtn, background: 'linear-gradient(135deg,#059669,#0d9488)', color: '#fff', border: 'none' }}>
              ✓ Finish
            </button>
          ) : (
            <button onClick={next} style={s.navBtn}>Next →</button>
          )}
        </div>

        {/* Route label */}
        <div style={s.routeTag}>📍 {current.route === '/' ? 'Home' : current.route}</div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
        @keyframes waveAnim { 0%,100% { transform: scaleY(0.4); } 50% { transform: scaleY(1.2); } }
      `}</style>
    </>
  )
}

/* ── Avatar styles ── */
const av = {
  wrap:    { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, position: 'relative', flexShrink: 0 },
  glowRing:{ position: 'absolute', top: -4, left: -4, width: 96, height: 96, borderRadius: '50%',
             background: 'conic-gradient(from 0deg, #1a56db, #7c3aed, #059669, #f59e0b, #1a56db)',
             opacity: 0.25, zIndex: 0 },
  body:    { position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' },
  waves:   { display: 'flex', gap: 3, alignItems: 'center', marginTop: 4 },
  wave:    { width: 3, height: 14, borderRadius: 99, background: '#1a56db', animation: 'waveAnim 0.6s ease-in-out infinite' },
  name:    { fontSize: 10, fontWeight: 700, color: '#64748b', letterSpacing: 0.3, marginTop: 2 },
}

/* ── Layout styles ── */
const s = {
  launchBtn:    { position: 'fixed', bottom: 24, right: 24, zIndex: 400, background: 'linear-gradient(135deg,#1a56db,#7c3aed)', color: '#fff',
                  border: 'none', borderRadius: 16, padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                  boxShadow: '0 8px 32px rgba(26,86,219,0.4)', fontFamily: 'inherit' },
  overlay:      { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', zIndex: 490, backdropFilter: 'blur(3px)' },
  card:         { position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 500,
                  background: '#0f172a', borderRadius: 24, width: 'min(92vw, 680px)',
                  boxShadow: '0 32px 80px rgba(0,0,0,0.7)', overflow: 'hidden', fontFamily: 'inherit' },
  progressTrack:{ height: 3, background: '#1e293b' },
  progressFill: { height: '100%', background: 'linear-gradient(90deg,#1a56db,#7c3aed,#059669)', borderRadius: 99, transition: 'width 0.6s ease' },
  header:       { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 20px', borderBottom: '1px solid #1e293b' },
  stepBadge:    { background: '#1e293b', color: '#94a3b8', borderRadius: 20, padding: '3px 10px', fontSize: 12, fontWeight: 700 },
  langBtn:      { background: '#1e293b', border: 'none', color: '#e2e8f0', borderRadius: 10, padding: '6px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' },
  langMenu:     { position: 'absolute', top: '110%', right: 0, background: '#1e293b', borderRadius: 12, padding: 6, border: '1px solid #334155',
                  display: 'flex', flexDirection: 'column', gap: 2, zIndex: 10, minWidth: 140, boxShadow: '0 8px 24px rgba(0,0,0,0.5)' },
  langOption:   { background: 'none', border: 'none', color: '#e2e8f0', borderRadius: 8, padding: '8px 12px', fontSize: 13, fontWeight: 600, cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit' },
  closeBtn:     { background: '#334155', border: 'none', color: '#94a3b8', borderRadius: 8, width: 28, height: 28, cursor: 'pointer', fontSize: 14, fontFamily: 'inherit' },
  body:         { display: 'flex', gap: 20, alignItems: 'flex-start', padding: '20px 20px 12px', minHeight: 140 },
  content:      { flex: 1, display: 'flex', flexDirection: 'column', gap: 6 },
  stepEmoji:    { fontSize: 28, lineHeight: 1, marginBottom: 2 },
  stepTitle:    { fontSize: 18, fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.3px', lineHeight: 1.2 },
  subtitleBox:  { fontSize: 14, color: '#94a3b8', lineHeight: 1.7, minHeight: 60, background: '#1e293b', borderRadius: 12, padding: '12px 14px', border: '1px solid #334155' },
  dots:         { display: 'flex', gap: 6, justifyContent: 'center', padding: '8px 20px' },
  dot:          { width: 8, height: 8, borderRadius: '50%', background: '#334155', border: 'none', cursor: 'pointer', padding: 0, transition: 'all 0.2s' },
  dotActive:    { background: '#1a56db', width: 22, borderRadius: 99 },
  dotDone:      { background: '#059669' },
  controls:     { display: 'flex', gap: 10, padding: '12px 20px', borderTop: '1px solid #1e293b', alignItems: 'center' },
  navBtn:       { flex: 1, background: '#1e293b', border: '1px solid #334155', color: '#e2e8f0', borderRadius: 12, padding: '10px', fontSize: 14, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' },
  pauseBtn:     { background: 'none', border: '1px solid #334155', color: '#64748b', borderRadius: 12, padding: '10px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap' },
  routeTag:     { fontSize: 11, color: '#475569', textAlign: 'center', padding: '6px 0 10px', letterSpacing: 0.3 },
}
