import os
try:
    import google.generativeai as genai
except ImportError:
    print("Chưa cài google-generativeai. Cài bằng: pip install google-generativeai")
    exit(1)

def check_gemini_api(api_key=None):
    api_key = api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("Nhập Gemini API key: ").strip()
    try:
        genai.configure(api_key=api_key)
        print("Các model khả dụng với key này:")
        available_models = []
        for m in genai.list_models():
            print(f"- {m.name} | methods: {m.supported_generation_methods}")
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        if not available_models:
            print("Không có model nào hỗ trợ generateContent với key này.")
            return
        model_name = available_models[0]
        print(f"\nThử gọi model: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello in Vietnamese")
        print("Gemini API hoạt động! Kết quả:")
        print(response.text if hasattr(response, 'text') else response)
    except Exception as e:
        print(f"Lỗi khi kiểm tra Gemini API: {e}")

if __name__ == "__main__":
    check_gemini_api() 