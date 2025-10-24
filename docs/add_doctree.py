import os

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(DOCS_DIR, "generated")

# Tìm tất cả file .rst trong docs/, trừ GINCCO_lib.rst và những file không phải module
rst_files = [
    f for f in os.listdir(DOCS_DIR)
    if f.startswith("GINCCO_lib.") and f.endswith(".rst") and f != "GINCCO_lib.rst"
]

for rst_file in rst_files:
    module_name = rst_file[:-4]  # bỏ .rst

    # Bỏ qua module bắt đầu bằng "_"
    if any(part.startswith("_") for part in module_name.split(".")):
        continue

    rst_path = os.path.join(DOCS_DIR, rst_file)

    # Nội dung block toctree cần thêm
    toctree_block = f"""

.. toctree::
   :maxdepth: 1
   :glob:

   generated/{module_name}.*
"""

    # Đọc nội dung hiện tại
    with open(rst_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Nếu đã có toctree rồi thì bỏ qua (để không chèn lặp)
    if "toctree::" in content:
        print(f"⏩ Skip {rst_file} (already has toctree)")
        continue

    # Ghi thêm block toctree vào cuối file
    with open(rst_path, "a", encoding="utf-8") as f:
        f.write(toctree_block)

    print(f"✅ Added toctree to {rst_file}")

print("\n🎉 Done! All module .rst files now include generated/ links.")
