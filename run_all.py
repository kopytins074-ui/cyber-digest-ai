"""
Скрипт для запуска всех этапов обработки новостей.
Запускает main.py, email_preview.py и post_generator.py по очереди.
"""

import subprocess
import sys

def run_script(script_name, step_number, total_steps):
    """Запускает скрипт и проверяет, что он завершился успешно."""
    print(f"\n[{step_number}/{total_steps}] Запуск {script_name}...")
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False,  # показываем вывод в консоль
        text=True
    )
    if result.returncode != 0:
        print(f"[!] Ошибка при выполнении {script_name}")
        return False
    return True


def main():
    print("=" * 50)
    print("ЗАПУСК ВСЕХ ЭТАПОВ")
    print("=" * 50)
    
    scripts = [
        "main.py",
        "email_preview.py",
        "post_generator.py"
    ]
    
    for i, script in enumerate(scripts, 1):
        success = run_script(script, i, len(scripts))
        if not success:
            print("\n[!] Процесс остановлен из-за ошибки.")
            return
    
    print("\n" + "=" * 50)
    print("ВСЁ ГОТОВО!")
    print("=" * 50)
    print("Созданные файлы:")
    print("  • digest.json — полный дайджест")
    print("  • email_preview.txt — предпросмотр письма")
    print("  • post.txt — пост для соцсетей")


if __name__ == "__main__":
    main()