import requests

def send_whatsapp_message(phone_number, api_key, message):
    url = "https://api.callmebot.com/whatsapp.php"
    payload = {
        "phone": phone_number,
        "text": message,
        "apikey": api_key
    }

    try:
        response = requests.get(url, params=payload)
        if "Message successfully sent" in response.text:
            print("✅ تم إرسال الرسالة بنجاح.")
        else:
            print("⚠️ لم يتم إرسال الرسالة:", response.text)
    except Exception as e:
        print("❌ حصل خطأ:", e)
