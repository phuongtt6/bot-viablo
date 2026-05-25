# bot-viablo

Bot tự động lấy bài viết mới nhất từ [viblo.asia/newest](https://viblo.asia/newest) qua RSS và gửi sang Telegram. Chạy mỗi giờ một lần bằng GitHub Actions, có dedupe để không gửi lặp lại.

## Cách hoạt động

1. GitHub Actions cron chạy mỗi giờ (`0 * * * *` UTC).
2. Script `viblo-telegram-bot.py` fetch RSS từ `https://viblo.asia/rss`.
3. So sánh với `sent.json` để lọc bài chưa gửi.
4. Gửi tối đa `MAX_POSTS` (mặc định 5) bài lên Telegram chat.
5. Commit `sent.json` cập nhật vào repo để giữ state.

## Setup

### 1. Tạo Telegram bot

1. Mở Telegram, chat với [@BotFather](https://t.me/BotFather).
2. Gõ `/newbot`, đặt tên và username — BotFather trả về **bot token** dạng `123456:ABC-DEF...`.
3. Tạo channel/group, **add bot vào và cấp quyền gửi tin**.
4. Lấy `chat_id`:
   - Với channel public: dùng `@channel_username`.
   - Với private group/channel: gửi 1 tin nhắn trong group, sau đó mở `https://api.telegram.org/bot<TOKEN>/getUpdates` để xem `chat.id` (group thường âm, ví dụ `-1001234567890`).

### 2. Cấu hình GitHub Secrets

Vào repo trên GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Giá trị |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token từ BotFather |
| `TELEGRAM_CHAT_ID` | ID channel/group |

### 3. Push lên GitHub

```bash
git add .
git commit -m "feat: viblo-to-telegram bot with hourly schedule"
git push origin main
```

Workflow tự kích hoạt theo cron. Có thể chạy thủ công ở tab **Actions** → **Viblo Telegram Bot** → **Run workflow**.

## Chạy local để test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python viblo-telegram-bot.py
```

Hoặc copy `.env.example` thành `.env` và `source` nó.

## Tuỳ chỉnh

- **Tần suất**: sửa `cron` trong `.github/workflows/viblo-telegram-bot.yml`. GitHub Actions chỉ chạy cron với độ chính xác ~10–15 phút, không nên đặt < 15 phút.
- **Số bài/lần**: sửa env `MAX_POSTS` (mặc định 5).
- **Feed khác**: đổi `VIBLO_RSS_URL` trong `viblo-telegram-bot.py` (ví dụ `https://viblo.asia/rss/tags/javascript`).

## File chính

- `viblo-telegram-bot.py` — script fetch + send.
- `requirements.txt` — `feedparser` + `requests`.
- `sent.json` — danh sách ID đã gửi (giữ tối đa 500 entry gần nhất).
- `.github/workflows/viblo-telegram-bot.yml` — cron workflow.
