# प्रॉपर्टीयार्ड्स बैकएंड

प्रॉपर्टीयार्ड्स रियल एस्टेट प्लेटफॉर्म के लिए FastAPI-आधारित बैकएंड सर्विस, जिसमें व्यापक सुविधाएं शामिल हैं जैसे प्रॉपर्टी मैनेजमेंट, यूजर ऑथेंटिकेशन, रिवॉर्ड्स सिस्टम, और एडवांस्ड कैशिंग।

## 🚀 सुविधाएं

### कोर फंक्शनैलिटी
- **प्रॉपर्टी मैनेजमेंट**: एडवांस्ड सर्च और फिल्टरिंग के साथ प्रॉपर्टी CRUD ऑपरेशन
- **यूजर ऑथेंटिकेशन**: JWT-आधारित ऑथेंटिकेशन रोल-आधारित एक्सेस कंट्रोल के साथ
- **पेमेंट प्रोसेसिंग**: मल्टीपल प्रोवाइडर के साथ सिक्योर पेमेंट इंटीग्रेशन
- **रिवॉर्ड्स सिस्टम**: कॉम्प्रिहेंसिव पॉइंट्स और कमीशन सिस्टम कन्वर्जन ऑप्शन के साथ
- **एनालिटिक्स**: रियल-टाइम एनालिटिक्स और रिपोर्टिंग कैपेबिलिटीज
- **AI इंटीग्रेशन**: AI-पावर्ड प्रॉपर्टी रिकमेंडेशन और SEO ऑप्टिमाइजेशन

### एडवांस्ड सुविधाएं
- **सिक्योरिटी**: एडवांस्ड थ्रेट डिटेक्शन, रेट लिमिटिंग, और इनपुट सैनिटाइजेशन
- **कैशिंग**: Redis-आधारित मल्टी-लेयर कैशिंग इंटेलिजेंट इनवेलिडेशन के साथ
- **मॉनिटरिंग**: परफॉर्मेंस मॉनिटरिंग और हेल्थ चेक्स
- **API डॉक्यूमेंटेशन**: ऑटो-जेनरेटेड OpenAPI/Swagger डॉक्यूमेंटेशन

## 🛠️ टेक स्टैक

- **फ्रेमवर्क**: FastAPI 0.104.1
- **डेटाबेस**: MongoDB Motor (async ड्राइवर) के साथ
- **कैश**: Redis aioredis के साथ
- **ऑथेंटिकेशन**: JWT python-jose के साथ
- **सिक्योरिटी**: bcrypt, slowapi रेट लिमिटिंग के लिए
- **टेस्टिंग**: pytest async सपोर्ट के साथ
- **डॉक्यूमेंटेशन**: OpenAPI/Swagger

## 🚀 त्वरित शुरुआत

### प्रीरिक्विजिट्स
- Python 3.8+
- MongoDB
- Redis
- Git

### इंस्टॉलेशन

1. **रिपॉजिटरी क्लोन करें**
   ```bash
   git clone https://github.com/your-org/propertyyards-backend.git
   cd propertyyards-backend
   ```

2. **वर्चुअल एनवायरनमेंट बनाएं**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows पर: venv\Scripts\activate
   ```

3. **डिपेंडेंसी इंस्टॉल करें**
   ```bash
   pip install -r requirements.txt
   ```

4. **एनवायरनमेंट वेरिएबल्स सेट करें**
   ```bash
   cp .env.example .env
   # .env को अपनी कॉन्फिग्यूरेशन के साथ एडिट करें
   ```

5. **सर्विसेज शुरू करें**
   ```bash
   # MongoDB और Redis को Docker के साथ शुरू करें
   docker-compose up -d mongodb redis

   # एप्लिकेशन चलाएं
   python run.py
   ```

### Docker सेटअप

```bash
# Docker के साथ बिल्ड और रन करें
docker-compose up -d

# लॉग देखें
docker-compose logs -f backend
```

## ⚙️ कॉन्फिग्यूरेशन

### एनवायरनमेंट वेरिएबल्स

```bash
# डेटाबेस
MONGODB_URL=mongodb://localhost:27017/housing_db
MONGO_ROOT_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# एप्लिकेशन
DEBUG=False
SECRET_KEY=your_app_secret
API_V1_STR=/api/v1
```

## 📚 API डॉक्यूमेंटेशन

एक बार सर्वर चलने के बाद, विजिट करें:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 प्रोजेक्ट स्ट्रक्चर

```
backend/
├── app/                    # एप्लिकेशन कोड
│   ├── api/               # API रूट्स
│   ├── auth.py            # ऑथेंटिकेशन लॉजिक
│   ├── cache.py           # कैशिंग लेयर
│   ├── config.py          # कॉन्फिग्यूरेशन
│   ├── database.py        # डेटाबेस कनेक्शन
│   ├── models.py          # डेटा मॉडल्स
│   ├── security.py        # सिक्योरिटी मिडलवेयर
│   └── services/          # बिजनेस लॉजिक
├── tests/                 # टेस्ट सूट
├── scripts/               # यूटिलिटी स्क्रिप्ट्स
├── requirements.txt       # Python डिपेंडेंसी
├── pyproject.toml         # प्रोजेक्ट कॉन्फिग्यूरेशन
├── Dockerfile             # Docker कॉन्फिग्यूरेशन
├── docker-compose.yml     # डेवलपमेंट सर्विसेज
└── README.md              # यह फाइल
```

## 🧪 डेवलपमेंट

### टेस्ट चलाना

```bash
# सभी टेस्ट चलाएं
pytest

# कवरेज के साथ चलाएं
pytest --cov=app

# विशिष्ट टेस्ट फाइल चलाएं
pytest tests/test_auth.py
```

### कोड क्वालिटी

```bash
# कोड फॉर्मेट करें
black app/ tests/

# कोड लिंट करें
flake8 app/ tests/

# टाइप चेकिंग
mypy app/
```

### डेटाबेस माइग्रेशन

```bash
# डेटाबेस इनिशियलाइज़ करें
python -m app.init_db

# इंडेक्स बनाएं
python -m app.create_indexes
```

## 🔌 API एंडपॉइंट्स

### ऑथेंटिकेशन
- `POST /api/auth/login` - यूजर लॉगिन
- `POST /api/auth/register` - यूजर रजिस्ट्रेशन
- `POST /api/auth/refresh` - रिफ्रेश टोकन
- `POST /api/auth/logout` - यूजर लॉगआउट

### प्रॉपर्टीज
- `GET /api/properties` - प्रॉपर्टी लिस्ट
- `POST /api/properties` - प्रॉपर्टी बनाएं
- `GET /api/properties/{id}` - प्रॉपर्टी प्राप्त करें
- `PUT /api/properties/{id}` - प्रॉपर्टी अपडेट करें
- `DELETE /api/properties/{id}` - प्रॉपर्टी डिलीट करें

### रिवॉर्ड्स
- `GET /api/rewards/wallet` - रिवॉर्ड्स वॉलेट प्राप्त करें
- `POST /api/rewards/convert-points` - पॉइंट्स को कैश में कन्वर्ट करें
- `GET /api/rewards/conversion/history` - कन्वर्जन हिस्ट्री
- `GET /api/rewards/referral/code` - रेफरल कोड प्राप्त करें

### एडमिन
- `GET /api/admin/stats` - सिस्टम स्टैटिस्टिक्स
- `POST /api/admin/process-commission` - कमीशन प्रोसेस करें
- `GET /api/admin/users` - यूजर मैनेजमेंट

## 🔒 सिक्योरिटी सुविधाएं

### थ्रेट डिटेक्शन
- SQL इंजेक्शन प्रोटेक्शन
- XSS अटैक डिटेक्शन
- पाथ ट्रैवर्सल प्रिवेंशन
- प्रति एंडपॉइंट रेट लिमिटिंग
- संदिग्ध गतिविधि के लिए IP ब्लॉकिंग

### ऑथेंटिकेशन और ऑथराइजेशन
- JWT टोकन-आधारित ऑथेंटिकेशन
- रोल-आधारित एक्सेस कंट्रोल (RBAC)
- सेशन मैनेजमेंट
- मल्टी-फैक्टर ऑथेंटिकेशन सपोर्ट

### डेटा प्रोटेक्शन
- इनपुट सैनिटाइजेशन और वेलिडेशन
- bcrypt के साथ पासवर्ड हैशिंग
- CORS कॉन्फिग्यूरेशन
- सिक्योरिटी हेडर्स मिडलवेयर

## 🚀 कैशिंग स्ट्रैटेजी

### मल्टी-लेयर कैशिंग
- **L1**: एप्लिकेशन-लेवल कैशिंग
- **L2**: Redis डिस्ट्रिब्यूटेड कैशिंग
- **L3**: डेटाबेस क्वेरी कैशिंग

### कैश सुविधाएं
- इंटेलिजेंट इनवेलिडेशन
- फ्रिक्वेंटली एक्सेस्ड डेटा के लिए कैश वॉर्मिंग
- परफॉर्मेंस मॉनिटरिंग और मेट्रिक्स
- कैश फेल्योर के लिए फॉलबैक मैकेनिज्म

## 📊 मॉनिटरिंग और लॉगिंग

### हेल्थ चेक्स
- `/health` - बेसिक हेल्थ चेक
- `/health/detailed` - डिटेल्ड सिस्टम हेल्थ
- `/metrics` - एप्लिकेशन मेट्रिक्स

### लॉगिंग
- स्ट्रक्चर्ड JSON लॉगिंग
- रिक्वेस्ट/रिस्पॉन्स लॉगिंग
- एरर ट्रैकिंग और अलर्टिंग
- परफॉर्मेंस मॉनिटरिंग

## 🚀 डिप्लॉयमेंट

### प्रोडक्शन डिप्लॉयमेंट

```bash
# प्रोडक्शन इमेज बिल्ड करें
docker build -t propertyyards-backend .

# प्रोडक्शन कॉन्फिग्यूरेशन के साथ रन करें
docker run -d --name backend \
  -e MONGODB_URL=mongodb://mongo:27017/housing_db \
  -e REDIS_URL=redis://redis:6379/0 \
  -p 8000:8000 \
  propertyyards-backend
```

### एनवायरनमेंट-स्पेसिफिक कॉन्फिग्स

- **डेवलपमेंट**: डिबग मोड, लोकल डेटाबेस
- **स्टेजिंग**: प्रोडक्शन-जैसा सेटअप टेस्ट डेटा के साथ
- **प्रोडक्शन**: ऑप्टिमाइज्ड कॉन्फिग्यूरेशन, मॉनिटरिंग एनेबल्ड

## 🎯 परफॉर्मेंस ऑप्टिमाइजेशन

### डेटाबेस ऑप्टिमाइजेशन
- MongoDB इंडेक्सिंग स्ट्रैटेजी
- कनेक्शन पूलिंग
- क्वेरी ऑप्टिमाइजेशन
- डेटा आर्काइविंग पॉलिसीज

### API ऑप्टिमाइजेशन
- रिस्पॉन्स कंप्रेशन
- बड़े डेटासेट के लिए पेजिनेशन
- कैशिंग स्ट्रैटेजीज
- Async/await पैटर्न

### मेमोरी मैनेजमेंट
- कनेक्शन रियूज
- मेमोरी प्रोफाइलिंग
- गारबेज कलेक्शन ऑप्टिमाइजेशन
- रिसोर्स क्लीनअप

## 🤝 कंट्रिब्यूटिंग

1. रिपॉजिटरी फोर्क करें
2. फीचर ब्रांच बनाएं (`git checkout -b feature/amazing-feature`)
3. अपने चेंजेस कमिट करें (`git commit -m 'Add amazing feature'`)
4. ब्रांच पर पुश करें (`git push origin feature/amazing-feature`)
5. पुल रिक्वेस्ट खोलें

## 📄 लाइसेंस

यह प्रोजेक्ट MIT लाइसेंस के तहत लाइसेंस प्राप्त है - [LICENSE](LICENSE) फाइल विवरण के लिए देखें।

## 📞 सपोर्ट

- **डॉक्यूमेंटेशन**: [API डॉक्यूमेंटेशन](http://localhost:8000/docs)
- **इश्यूज**: [GitHub इश्यूज](https://github.com/your-org/propertyyards-backend/issues)
- **डिस्कशन**: [GitHub डिस्कशन](https://github.com/your-org/propertyyards-backend/discussions)

## 🔗 संबंधित रिपॉजिटरीज

- [फ्रंटएंड रिपॉजिटरी](https://github.com/your-org/propertyyards-frontend)
- [इंफ्रास्ट्रक्चर रिपॉजिटरी](https://github.com/your-org/propertyyards-infrastructure)
- [डॉक्यूमेंटेशन रिपॉजिटरी](https://github.com/your-org/propertyyards-docs)
