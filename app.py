import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE設定（環境変数から取得）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境変数が不足しています。")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 🔍 東京の天気を気象庁APIから取得
def get_tokyo_weather_jma():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 今日の天気（エリアによって index[0] が東京地方）
        today_forecast = data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
        return f"東京の今日の天気：{today_forecast}"
    except Exception as e:
        print("天気取得エラー:", e)
        return "天気情報を取得できませんでした。"

# 📩 メッセージ受信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()

    if "天気" in user_message:
        weather_info = get_tokyo_weather_jma()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_info))
    else:
        reply_message = f"あなたは「{event.message.text}」と言いました。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
