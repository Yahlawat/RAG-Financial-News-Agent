from transformers.pipelines import pipeline


try:
    pipe = pipeline("text-generation", model="tiiuae/falcon-rw-1b", local_files_only=True)
    print("✅ Model loaded locally.")
except Exception as e:
    print("❌ Model not found locally:", e)
