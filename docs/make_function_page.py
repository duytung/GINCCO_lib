import os
import importlib
import inspect


# Lấy thư mục chứa script (docs/)
DOCS_DIR = os.path.dirname(os.path.abspath(__file__)) or os.getcwd()
GENERATED_DIR = os.path.join(DOCS_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# 1️⃣ Lấy danh sách tất cả file .rst trong docs/, trừ file GINCCO_lib.rst
rst_files = [
    f for f in os.listdir(DOCS_DIR)
    if f.startswith("GINCCO_lib.") and f.endswith(".rst") and f != "GINCCO_lib.rst"
]

for rst_file in rst_files:
    module_name = rst_file[:-4]  # bỏ .rst

    # Bỏ qua module có tên private (bắt đầu bằng _)
    if any(part.startswith("_") for part in module_name.split(".")):
        continue

    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        print(f"⚠️  Skip {module_name} (cannot import: {e})")
        continue

    print(f"📘 Processing module: {module_name}")

    # 2️⃣ Lấy danh sách function public (không bắt đầu bằng _)
    functions = [
        (name, func)
        for name, func in inspect.getmembers(mod, inspect.isfunction)
        if not name.startswith("_")
    ]

    # 3️⃣ Sinh file .rst cho từng function
    for name, func in functions:
        rst_path = os.path.join(GENERATED_DIR, f"{module_name}.{name}.rst")
        os.makedirs(os.path.dirname(rst_path), exist_ok=True)
        with open(rst_path, "w", encoding="utf-8") as f:
            f.write(f"{name}\n{'=' * len(name)}\n\n")
            f.write(f".. autofunction:: {module_name}.{name}\n")
        print(f"   ✅ Generated {os.path.basename(rst_path)}")

print("\n🎉 Done! Generated files are in:", GENERATED_DIR)
