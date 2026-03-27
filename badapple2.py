import cv2 as cv
import numpy as np
import time
import subprocess
import os
import random
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

# ── 設定區 ──────────────────────────────────────────
WHITE_TEXT  = "呂思儀李虹瑩鄭鈞賢葉紘愷"
EMOJI_LIST  = ["😀", "💩", "👻", "😆", "😂", "😇", "🤪", "🤩"]

CELL_SIZE   = 16
THRESHOLD   = 127
FONT_SIZE   = 14
TEXT_SIZE   = 11

CANNY_LOW   = 50
CANNY_HIGH  = 150

TEXT_FONT_PATH  = "C:/Windows/Fonts/kaiu.ttf"   


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception as e:
        print(f"找不到字體 '{path}'：{e}")
        return ImageFont.load_default()


def render_frame(frame, text_font, cell_size, threshold):
    h, w = frame.shape[:2]
    gray  = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    edges = cv.Canny(gray, CANNY_LOW, CANNY_HIGH)

    pil_img = Image.new("RGB", (w, h), (255, 255, 255))

    white_chars = list(WHITE_TEXT)
    char_index  = 0

    rows = h // cell_size
    cols = w // cell_size

    with Pilmoji(pil_img) as draw:
        for row in range(rows):
            for col in range(cols):
                y1 = row * cell_size
                x1 = col * cell_size
                y2 = min(y1 + cell_size, h)
                x2 = min(x1 + cell_size, w)

                avg_brightness = np.mean(gray[y1:y2, x1:x2])
                has_edge       = np.any(edges[y1:y2, x1:x2] > 0)

                if avg_brightness < threshold:
                    if has_edge:
                       
                        emoji = random.choice(EMOJI_LIST)
                        draw.text((x1, y1), emoji, font=text_font)
                    else:
                       
                        ImageDraw.Draw(pil_img).rectangle(
                            [x1, y1, x2, y2], fill=(255, 255, 255)
                        )
                else:
                    
                    char = white_chars[char_index % len(white_chars)]
                    draw.text((x1 + 1, y1), char, font=text_font, fill=(180, 180, 180))
                    char_index += 1

    return cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)


def create_video(input_path, output_path):
    temp_video = output_path.replace(".mp4", "_silent.mp4")

    video = cv.VideoCapture(input_path)
    if not video.isOpened():
        print(f"找不到影片：'{input_path}'")
        return

    fps          = video.get(cv.CAP_PROP_FPS)
    width        = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
    height       = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv.CAP_PROP_FRAME_COUNT))

    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out    = cv.VideoWriter(temp_video, fourcc, fps, (width, height))

    text_font = get_font(TEXT_FONT_PATH, TEXT_SIZE)

    print(f"開始處理：{total_frames}，字元格：{CELL_SIZE}px")
    print("💡 pilmoji 第一次執行會從網路抓 emoji 圖片，請稍候...")
    print("💡 按視窗上的 'q' 鍵可提早結束。")

    start_time = time.time()
    count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        count += 1
        canvas = render_frame(frame, text_font, CELL_SIZE, THRESHOLD)
        out.write(canvas)

        cv.imshow('Bad Apple Emoji  (Q to stop)', canvas)

        if count % 100 == 0:
            elapsed = time.time() - start_time
            pct     = count / total_frames * 100
            speed   = count / elapsed
            print(f"⏳ {count}/{total_frames} ({pct:.1f}%) | {speed:.1f} fps | {elapsed:.1f}s")

        if cv.waitKey(1) & 0xFF == ord('q'):
            print("\n中斷，正在儲存...")
            break

    video.release()
    out.release()
    cv.destroyAllWindows()

    print("\n正在合併原始音訊...")
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", input_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        os.remove(temp_video)
        total_time = time.time() - start_time
        print(f"\n完成！總耗時：{total_time:.1f} 秒")
        print(f"📁 已儲存至：{output_path}")
    else:
        print("ffmpeg 合併失敗，無聲版保存在：", temp_video)
        print("錯誤訊息：", result.stderr[-500:].decode("utf-8", errors="ignore"))


if __name__ == "__main__":
    create_video(
        input_path="bad_apple.mp4",
        output_path="bad_apple_emoji.mp4",
    )