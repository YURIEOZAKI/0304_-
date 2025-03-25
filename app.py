import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からLINEのシークレット情報を取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # 天気APIキー

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN or not OPENWEATHER_API_KEY:
    raise ValueError("環境変数が不足しています。")

# LINE APIのセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # X-Line-Signatureヘッダーの取得
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    print("Received Body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 東京の天気情報を取得
def get_weather_tokyo():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]

        return f"東京の現在の天気は「{weather}」、気温は{temp}℃（体感 {feels_like}℃）です。"
    except Exception as e:
        print("Error fetching weather:", e)
        return "天気情報を取得できませんでした。"

# メッセージハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()

    if "今日の天気" in user_message or "天気" in user_message:
        weather_info = get_weather_tokyo()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_info))
    else:
        reply_message = f"あなたは「{event.message.text}」と言いました。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
