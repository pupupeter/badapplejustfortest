import cv2 as cv
import numpy as np
import time
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

WHITE_TEXT  = "Thisisjustforfun"
BLACK_TEXT  = "ㅋ"
CELL_SIZE   = 12
THRESHOLD   = 127
FONT_SIZE   = 11
CANNY_LOW   = 50
CANNY_HIGH  = 150

FONT_PATH = "C:/Windows/Fonts/malgun.ttf"  #


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        print(f"⚠️  找不到字體 '{path}'，使用預設字體")
        return ImageFont.load_default()


def render_frame(frame, font, cell_size, threshold):
    h, w = frame.shape[:2]
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # 偵測輪廓邊緣
    edges = cv.Canny(gray, CANNY_LOW, CANNY_HIGH)

    pil_img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(pil_img)

    white_chars = list(WHITE_TEXT)
    char_index = 0

    rows = h // cell_size
    cols = w // cell_size

    for row in range(rows):
        for col in range(cols):
            y1 = row * cell_size
            x1 = col * cell_size
            y2 = min(y1 + cell_size, h)
            x2 = min(x1 + cell_size, w)

            cell_gray  = gray[y1:y2, x1:x2]
            cell_edges = edges[y1:y2, x1:x2]

            avg_brightness = np.mean(cell_gray)
            has_edge       = np.any(cell_edges > 0)  # 此格有輪廓線？

            if avg_brightness < threshold:
                if has_edge:
                    
                    draw.text((x1 + 1, y1), BLACK_TEXT, font=font, fill=(0, 0, 0))
                else:
                    
                    draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))
            else:
                
                char = white_chars[char_index % len(white_chars)]
                draw.text((x1 + 1, y1), char, font=font, fill=(180, 180, 180))
                char_index += 1

    return cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)


def create_video(input_path, output_path):
    temp_video = output_path.replace(".mp4", "_silent.mp4")

    video = cv.VideoCapture(input_path)
    if not video.isOpened():
        print(f"❌ 找不到影片：'{input_path}'")
        return

    fps          = video.get(cv.CAP_PROP_FPS)
    width        = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
    height       = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv.CAP_PROP_FRAME_COUNT))

    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out    = cv.VideoWriter(temp_video, fourcc, fps, (width, height))
    font   = get_font(FONT_PATH, FONT_SIZE)

    print(f"🚀 開始處理！總幀數：{total_frames}，字元格：{CELL_SIZE}px")
    print("💡 按視窗上的 'q' 鍵可提早結束。")

    start_time = time.time()
    count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        count += 1
        canvas = render_frame(frame, font, CELL_SIZE, THRESHOLD)
        out.write(canvas)

        cv.imshow('Bad Apple ㅋ  (Q to stop)', canvas)

        if count % 100 == 0:
            elapsed = time.time() - start_time
            pct     = count / total_frames * 100
            speed   = count / elapsed
            print(f"⏳ {count}/{total_frames} ({pct:.1f}%) | {speed:.1f} fps | {elapsed:.1f}s")

        if cv.waitKey(1) & 0xFF == ord('q'):
            print("\n⚠️ 中斷，正在儲存...")
            break

    video.release()
    out.release()
    cv.destroyAllWindows()

    print("\n🔊 正在合併原始音訊...")
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
        print(f"\n🎉 完成！總耗時：{total_time:.1f} 秒")
        print(f"📁 已儲存至：{output_path}")
    else:
        print("❌ ffmpeg 合併失敗，無聲版保存在：", temp_video)
        print("錯誤訊息：", result.stderr[-500:].decode("utf-8", errors="ignore"))


if __name__ == "__main__":
    create_video(
        input_path="bad_apple.mp4",
        output_path="bad_apple_ㅋ.mp4",
    )