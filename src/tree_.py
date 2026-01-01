import os

def generate_project_summary(root_dir, output_file):
    # الملفات أو الفولدرات اللي عايز نتجاهلها (عشان الزحمة)
    exclude = {'.git', '__pycache__', '.pytest_cache', '.vscode', 'node_modules', '.idea'}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"PROJECT STRUCTURE & CONTENT\n")
        f.write(f"Root: {os.path.abspath(root_dir)}\n")
        f.write("="*50 + "\n\n")

        # 1. رسم الهيكل الشجري في أول الملف
        f.write("--- DIRECTORY TREE ---\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude] # تجاهل الفولدرات المحددة
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent} {os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f"{sub_indent} {file}\n")
        
        f.write("\n" + "="*50 + "\n\n")

        # 2. كتابة محتوى كل ملف
        f.write("--- FILE CONTENTS ---\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file == output_file: continue # متكتبش محتوى ملف النتيجة نفسه
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_dir)
                
                f.write(f"\n[ FILE: {relative_path} ]\n")
                f.write("-" * (len(relative_path) + 10) + "\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as source_file:
                        f.write(source_file.read())
                except Exception as e:
                    f.write(f"<< Could not read file: {e} >>")
                
                f.write("\n\n" + "*"*30 + "\n")

if __name__ == "__main__":
    # بيشتغل في المجلد الحالي
    current_directory = os.getcwd()
    output_name = "project_summary.txt"
    
    print(f"Generating summary for: {current_directory}")
    generate_project_summary(current_directory, output_name)
    print(f"Done! Check {output_name}")