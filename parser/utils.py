import zipfile
import os

def zip_output(folder, output):
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)
                z.write(path)