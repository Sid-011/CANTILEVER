from PIL import Image
import pytesseract

# 1️⃣ Set path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hd c\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# 2️⃣ Path to your image
image_path = r"C:\Users\hd c\Desktop\Task\TASK 2\02.png"

# 3️⃣ Open image
img = Image.open(image_path)

# 4️⃣ Perform OCR
text = pytesseract.image_to_string(img)

# 5️⃣ Print extracted text
print("OCR Output:\n", text)