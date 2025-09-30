import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class QuestionManager:
    """
    题目管理器类。
    负责加载、导入和查询题库数据库 (questions.json)。
    """

    def __init__(self, database_path: str):
        """
        初始化题目管理器。

        Args:
            database_path: 题库数据库文件 (questions.json) 的路径。
        """
        self.database_path = database_path
        self.questions: List[Dict[str, Any]] = []
        self._load_database()

    def _load_database(self):
        """
        从 JSON 文件加载题库数据。
        如果文件不存在或为空，则初始化一个空列表。
        """
        try:
            if os.path.exists(self.database_path) and os.path.getsize(self.database_path) > 0:
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    self.questions = json.load(f)
            else:
                self.questions = []
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"警告: 数据库文件 '{self.database_path}' 不存在或格式错误。将初始化为空题库。")
            self.questions = []

    def _save_database(self):
        """
        将当前内存中的题库数据完整地写入到 JSON 文件中。
        """
        try:
            with open(self.database_path, 'w', encoding='utf-8') as f:
                # 使用 indent=2 格式化输出，ensure_ascii=False 支持中文
                json.dump(self.questions, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"错误: 无法写入数据库文件 '{self.database_path}': {e}")

    def import_question_from_file(self, source_file_path: str) -> Optional[Dict[str, Any]]:
        """
        从单个 JSON 文件导入一道题目到题库中。

        Args:
            source_file_path: 包含单道题目的源 JSON 文件路径。

        Returns:
            处理并添加到题库后的题目字典 (包含新的 questionId)，如果导入失败则返回 None。
        """
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                question_data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 导入文件未找到: {source_file_path}")
            return None
        except json.JSONDecodeError:
            print(f"错误: 无法解析导入文件: {source_file_path}")
            return None

        # --- 关键数据处理步骤 ---
        # 1. 生成唯一的 UUID 替换原有的 questionId
        new_id = str(uuid.uuid4())
        question_data['questionId'] = new_id

        # 2. (可选) 添加导入时间戳
        question_data['importTimestampUTC'] = datetime.utcnow().isoformat()

        # 3. 将处理后的题目添加到内存列表
        self.questions.append(question_data)

        # 4. 持久化保存到文件
        self._save_database()

        print(f"✅ 成功导入题目，新 ID 为: {new_id}")
        return question_data

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 questionId 查找题目。

        Args:
            question_id: 要查找的题目ID。

        Returns:
            找到的题目字典，如果未找到则返回 None。
        """
        for q in self.questions:
            if q.get('questionId') == question_id:
                return q
        return None

    def get_questions_by_kpid(self, kpid: str) -> List[Dict[str, Any]]:
        """
        根据知识点ID (KPID) 查找所有关联的题目。

        Args:
            kpid: 知识点编码。

        Returns:
            一个包含所有匹配题目的列表。
        """
        matched_questions = []
        for q in self.questions:
            # 确保 metadata 和 knowledgePointIds 存在且是一个列表
            if kpid in q.get('metadata', {}).get('knowledgePointIds', []):
                matched_questions.append(q)
        return matched_questions

    def get_total_questions(self) -> int:
        """返回题库中的题目总数。"""
        return len(self.questions)

# --- 以下是用于测试的代码 ---
if __name__ == "__main__":
    # 定义数据库和导入文件的路径
    DB_FILE = os.path.join("data", "questions.json")
    IMPORT_Q1_FILE = os.path.join("data", "imports", "q1.json")
    IMPORT_Q2_FILE = os.path.join("data", "imports", "q2.json")

    print("--- 初始化题目管理器 ---")
    # 每次测试前，可以选择清空旧的数据库文件，以便从头开始
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"已清空旧的数据库文件: {DB_FILE}")

    q_manager = QuestionManager(DB_FILE)
    print(f"管理器初始化完成。当前题库中有 {q_manager.get_total_questions()} 道题。")
    print("-" * 20)

    print("\n--- 开始导入题目 ---")
    # 1. 导入第一道题
    print(f"正在从 '{IMPORT_Q1_FILE}' 导入...")
    imported_q1 = q_manager.import_question_from_file(IMPORT_Q1_FILE)
    if imported_q1:
        # 保存新ID用于后续测试
        new_q1_id = imported_q1.get('questionId')

    # 2. 导入第二道题
    print(f"\n正在从 '{IMPORT_Q2_FILE}' 导入...")
    q_manager.import_question_from_file(IMPORT_Q2_FILE)
    print("-" * 20)

    print(f"\n--- 导入完成 ---")
    print(f"当前题库中总共有 {q_manager.get_total_questions()} 道题。")
    print("-" * 20)

    print("\n--- 测试查询功能 ---")
    # 3. 测试按ID查询
    if 'new_q1_id' in locals():
        print(f"正在用 ID '{new_q1_id[:8]}...' 查询第一道题...")
        found_q1 = q_manager.get_question_by_id(new_q1_id)
        if found_q1:
            print(f"✅ 查询成功！题目题干: '{found_q1.get('stem')}'")
        else:
            print("❌ 查询失败！")

    # 4. 测试按KPID查询
    test_kpid = "BIO-B1-C02-S01-T02-A02"
    print(f"\n正在用 KPID '{test_kpid}' 查询关联题目...")
    found_by_kpid = q_manager.get_questions_by_kpid(test_kpid)
    print(f"✅ 查询到 {len(found_by_kpid)} 道相关题目。")
    if found_by_kpid:
        print(f"   - 题干: '{found_by_kpid[0].get('stem')}'")