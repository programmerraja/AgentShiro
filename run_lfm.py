import sys
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch
import time


image_path = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "/app/images/screenshot_2026-04-17_10-41-09.png"
)
prompt = sys.argv[2] if len(sys.argv) > 2 else "Describe this image."

model_id = "LiquidAI/LFM2.5-VL-450M"

model = AutoModelForImageTextToText.from_pretrained(
    model_id, device_map="auto", torch_dtype=torch.bfloat16
)
processor = AutoProcessor.from_pretrained(model_id)

image = Image.open(image_path).convert("RGB")

conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt},
        ],
    }
]

inputs = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
    return_tensors="pt",
    return_dict=True,
    tokenize=True,
).to(model.device)
start_time = time.time()
outputs = model.generate(**inputs, max_new_tokens=128)
end_time = time.time()
print(processor.batch_decode(outputs, skip_special_tokens=True)[0])
print(f"\nTime taken: {end_time - start_time:.3f} seconds")


# docker run --rm -it -v /home/boopathik/screenshots:/app/images -v /home/boopathik/.cache/huggingface:/root/.cache/huggingface lfm-vl-450m

# docker build -t lfm-vl-450m .
