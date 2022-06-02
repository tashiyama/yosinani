from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os
import wikipedia # 追加

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

wikipedia.set_lang("ja") # 追加

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
# 先ほどの関数内にWikipediaのライブラリを使った処理を記述していく
def handle_message(event):
    send_message = event.message.text
    # 正常に検索結果が返った場合
    try:
        wikipedia_page = wikipedia.page(send_message)
        # wikipedia.page()の処理で、ページ情報が取得できれば、以下のようにタイトル、リンク、サマリーが取得できる。
        wikipedia_title = wikipedia_page.title
        wikipedia_url = wikipedia_page.url
        wikipedia_summary = wikipedia.summary(send_message)
        reply_message = '【' + wikipedia_title + '】\n' + wikipedia_summary + '\n\n' + '【詳しくはこちら】\n' + wikipedia_url
    # ページが見つからなかった場合
    except wikipedia.exceptions.PageError:
        reply_message = '【' + send_message + '】\nについての情報は見つかりませんでした。'
    # 曖昧さ回避にひっかかった場合
    except wikipedia.exceptions.DisambiguationError as e:
        disambiguation_list = e.options
        reply_message = '複数の候補が返ってきました。以下の候補から、お探しの用語に近いものを再入力してください。\n\n'
        for word in disambiguation_list:
            reply_message += '・' + word + '\n'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(reply_message)
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)