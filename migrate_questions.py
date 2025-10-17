import json
import os
import shutil
from datetime import datetime

# --- 配置 ---
DB_FILE_PATH = os.path.join("data", "questions.json")
BACKUP_FILE_PATH = os.path.join("data", f"questions.json.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}")

def run_migration():
    """
    执行一次性的数据迁移，为旧格式的题目添加新的层级字段。
    """
    print("🚀 开始执行题目数据库迁移...")

    # 1. 检查数据库文件是否存在
    if not os.path.exists(DB_FILE_PATH):
        print(f"🟡 文件 '{DB_FILE_PATH}' 不存在，无需迁移。")
        return

    # 2. 创建安全备份
    try:
        shutil.copyfile(DB_FILE_PATH, BACKUP_FILE_PATH)
        print(f"✅ 已成功创建备份文件: '{BACKUP_FILE_PATH}'")
    except Exception as e:
        print(f"❌ 错误：创建备份文件失败: {e}")
        print("迁移已中止，您的原始文件未被修改。")
        return

    # 3. 读取数据并执行迁移
    try:
        with open(DB_FILE_PATH, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ 错误：读取或解析数据库文件失败: {e}")
        print("迁移已中止。")
        return

    migrated_count = 0
    skipped_count = 0

    print(f"🔍 发现 {len(questions)} 道题目，正在检查并迁移...")

    for question in questions:
        # 检查是否需要迁移 (幂等性)
        if 'structureType' in question and 'parentId' in question:
            skipped_count += 1
            continue

        # 为旧格式题目添加新字段
        question['structureType'] = 'ATOMIC'
        question['parentId'] = None
        migrated_count += 1

    # 4. 写回更新后的数据
    if migrated_count > 0:
        try:
            with open(DB_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"💾 已将更新后的数据写回 '{DB_FILE_PATH}'")
        except IOError as e:
            print(f"❌ 错误：写回更新后的数据失败: {e}")
            print("迁移失败，但您的原始数据已备份。")
            return
    else:
        print("✅ 所有题目均已是新格式，无需迁移。")


    print("\n--- 迁移完成 ---")
    print(f"  - 成功迁移: {migrated_count} 道题目")
    print(f"  - 跳过 (已是新格式): {skipped_count} 道题目")
    print("🎉 您的题库已成功升级到新架构！")


if __name__ == "__main__":
    run_migration()