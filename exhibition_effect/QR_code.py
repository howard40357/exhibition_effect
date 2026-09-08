import qrcode

# 1. 填入你部署好的 Streamlit 雲端網址
app_url = "http://localhost:8501/"

# 2. 建立 QR Code 物件
qr = qrcode.QRCode(
    version=1,  # 控制 QR Code 尺寸 (1-40)
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # 高容錯率，即使貼上 Logo 也能掃描
    box_size=10,  # 每個方格的像素大小
    border=4,  # 邊框寬度
)

qr.add_data(app_url)
qr.make(fit=True)

# 3. 產出圖片並存檔
img = qr.make_image(fill_color="black", back_color="white")
img.save("portfolio_qr.png")

print("QR Code 圖片已成功生成為 portfolio_qr.png！")