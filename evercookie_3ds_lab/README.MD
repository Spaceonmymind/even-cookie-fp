

# **evercookie_3ds — исследование устойчивого хранения идентификатора устройства**

Этот проект представляет собой экспериментальный стенд для проверки того, возможно ли **персистентно хранить идентификатор устройства** в браузере при использовании схемы, аналогичной **3DS Method (EMVCo)**, и техники **Evercookie (PNG-кэш + ETag + localStorage + IndexedDB)**.

Цель эксперимента — посмотреть реальное поведение **Safari**, чтобы оценить применимость такого подхода для антифрод-систем (например, MirAccept 2.0).

---

## **Структура репозитория**

```
evercookie_3ds_lab/
│
├── app_domain1.py        # Основной домен (ACS)
├── app_identserver.py    # Идентификационный сервер (iframe)
├── logs.jsonl            # Логи обращений и каналов хранения
├── test_results.json     # Результаты автотестов
│
└── tests/
    ├── test_browsers.py  # Selenium автотесты Safari
```

---

# **1. Что делает проект**

Проект реализует два режима:

### **Стенд A — CROSS-ORIGIN iframe**

* domain1.local загружает идентификационный сервер на identserver.local
* идентификация выполняется как third-party
* используется техника Evercookie:

  * cookie
  * localStorage
  * sessionStorage
  * IndexedDB
  * **PNG-кэш + ETag** (основной канал)

---

### **Стенд B — SAME-ORIGIN PROXY**

* iframe грузится как first-party
* запросы идентификатора проксируются через domain1.local
* попытка обойти ITP Safari через "own CDN" механизм

Этот режим аналогичен схемам Stape, Server-Side GTM и другим обходам tracking-ограничений.

---

# **2. Как запустить стенд локально**

### **Создать hosts-записи**

```
127.0.0.1 domain1.local
127.0.0.1 identserver.local
```

---

### **Установить зависимости**

```bash
pip install fastapi uvicorn pillow requests
```

---

### **Запустить оба сервера**

**Терминал 1:**

```bash
uvicorn app_domain1:app --host domain1.local --port 8000
```

**Терминал 2:**

```bash
uvicorn app_identserver:app --host identserver.local --port 8001
```

---

### **Открыть стенд**

```
http://domain1.local:8000
```

Вы увидите:

* Стенд A (CROSS-ORIGIN iframe)
* Стенд B (PROXY iframe)
* Логи
* Результаты автотестов

---

# **3. Как работает механизм Evercookie в проекте**

Проект реализует упрощённый, но эффективный Evercookie:

### **1. PNG-кэш + ETag**

UID кодируется в PNG 200×1:

* каждые 3 символа → один пиксель (R,G,B)
* остальные пиксели = (0,0,0) → признак конца строки

Ответ PNG содержит:

```
ETag: "<uid>"
Cache-Control: public, max-age=31536000, immutable
```

Если браузер вернул PNG из кэша → UID считается восстановленным.

---

### **2. Другие каналы хранения**

При открытии страницы identserver:

* cookie = device_id
* localStorage["device_id"]
* sessionStorage["device_id"]
* IndexedDB["device_id"]

UID восстанавливается в порядке приоритета:

```
cookie → localStorage → sessionStorage → IndexedDB → PNG-кэш
```

После восстановления UID записывается обратно во все каналы.

---

# **4. Автотесты (Selenium/WebDriver)**

Тест `tests/test_browsers.py`:

1. Запускает Safari
2. Заходит на стенд A или B
3. Считывает UID (первый заход)
4. Закрывает браузер
5. Открывает снова → считывает UID
6. Отправляет данные в `/save-test-result`

Результаты сохраняются в `test_results.json`.

---

# **5. Встроенный отчёт по эксперименту**

Ниже приведено краткое структурированное описание полученных результатов.

---

## **5.1. Safari — экспериментально подтверждённая невозможность устойчивого cross-origin хранения**

Safari **каждый раз** выдавал новый UID, несмотря на:

* cookie → всегда пусто
* localStorage → очищается
* sessionStorage → очищается
* IndexedDB → недоступна
* PNG-кэш → НЕ восстанавливается, UID меняется

Примеры UID из логов:

* `99b528952df864cd…`
* `60fc91c2055a68ba…`
* `cc90f2269ab40b2b…`

Это соответствует политике:

### **Safari ITP + Advanced Fingerprinting Protection**

* third-party storage = ephemeral
* ETag кэширован, но изолирован
* cookie заблокированы
* localStorage недоступен для iframe в третьей стороне
* IndexedDB сбрасывается

Safari **принципиально запрещает third-party fingerprinting**, поэтому Evercookie-подход невозможен.

---

## **5.2. Стенд B (proxy)**

Оба браузера возвращали “жду…” — стенд пока не завершён.
Выводы по Safari не меняются, так как проблема кроется в защитных политках WebKit.

---

# **6. Итоговые выводы**

### **1. Safari полностью блокирует persistent device ID в third-party iframe.**

Ни один из каналов Evercookie не работает.

### **2. Для 3DS Method / MirAccept 2.0:**

* device ID нельзя использовать как жёсткий идентификатор в Safari
* risk-based подход обязателен
* нужно собирать совокупность слабых сигналов вместо одного UID
* стабильный device ID возможен только в Chrome/Firefox

### **4. Рекомендация**

Использовать:

* probabilistic fingerprint,
* server-side корреляцию сессий,
* многофакторный risk scoring.

