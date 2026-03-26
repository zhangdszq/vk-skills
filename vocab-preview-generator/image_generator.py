import os
from volcengine.visual.VisualService import VisualService
from dotenv import load_dotenv

load_dotenv()

def generate_image_from_text(sentence: str) -> dict:
    """Generates an image from a given text sentence using Volcengine Visual Service.

    Args:
        sentence (str): The text sentence to generate the image from.

    Returns:
        dict: The response from the image generation service.
    """
    visual_service = VisualService()

    ak = os.getenv('VOLC_AK')
    sk = os.getenv('VOLC_SK')

    if not ak or not sk:
        return {
            "status": "error",
            "error_message": "Volcengine API keys (VOLC_AK, VOLC_SK) are not set in environment variables."
        }

    visual_service.set_ak(ak)
    visual_service.set_sk(sk)

    form = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": f"{sentence}. 精准帮我根据例句生成图片,风格一直为卡通，注意，一定图中不能有文字！, 图片主体要和例句单复数保持一致",
        "return_url": True
    }

    try:
        resp = visual_service.cv_process(form)
        if resp.get('data', {}).get('image_urls'):
            return {"status": "success", "image_url": resp['data']['image_urls'][0]}
        else:
            return {"status": "error", "error_message": "No image URL found in response."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

if __name__ == '__main__':
    # Example usage:
    # Make sure to set VOLC_AK and VOLC_SK in your .env file
    test_prompt = "I like to eat sweet <peaches>. 精准帮我根据例句生成图片,风格一直为卡通，注意，一定图中不能有文字！, 图片主体要和例句单复数保持一致"
    result = generate_image_from_text(test_prompt)
    print(result)