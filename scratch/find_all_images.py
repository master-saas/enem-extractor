import os

q_dir = "result/2025/questions"
if not os.path.exists(q_dir):
    print(f"Directory {q_dir} does not exist.")
else:
    found_any = False
    for root, dirs, files in os.walk(q_dir):
        for f in files:
            if f.endswith(".png"):
                found_any = True
                print(f"Found image: {os.path.join(root, f)}")
    if not found_any:
        print("No PNG images found in questions folder.")
