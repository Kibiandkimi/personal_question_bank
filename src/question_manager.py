import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class QuestionManager:
    """
    题目管理器类 (重构版)。
    支持单个或批量题目导入。
    """

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.questions: List[Dict[str, Any]] = []
        self._load_database()

    def _load_database(self):
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
        try:
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(self.questions, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"错误: 无法写入数据库文件 '{self.database_path}': {e}")

    # --- 新增的私有核心方法 ---
    def _add_question_object(self, question_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单个题目对象：生成ID、添加时间戳并添加到内存中。

        Args:
            question_data: 单个题目的字典。

        Returns:
            处理后的题目字典，如果数据无效则返回 None。
        """
        if not isinstance(question_data, dict):
            return None

        # 1. 生成唯一的 UUID 替换原有的 questionId
        new_id = str(uuid.uuid4())
        question_data['questionId'] = new_id

        # 2. 添加导入时间戳
        question_data['importTimestampUTC'] = datetime.utcnow().isoformat()

        # 3. 将处理后的题目添加到内存列表
        self.questions.append(question_data)

        return question_data

    # --- 重构后的导入方法 ---
    def import_question_from_file(self, source_file_path: str) -> int:
        """
        从 JSON 文件导入一道或多道题目到题库中。
        文件内容可以是单个JSON对象，也可以是JSON对象组成的列表。

        Args:
            source_file_path: 源 JSON 文件路径。

        Returns:
            成功导入的题目数量。
        """
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"错误: 无法读取或解析文件 '{source_file_path}': {e}")
            return 0

        imported_count = 0

        # 判断数据是单个对象还是对象列表
        if isinstance(data, dict):
            # 单个题目
            if self._add_question_object(data):
                imported_count = 1
        elif isinstance(data, list):
            # 批量题目
            for question_obj in data:
                if self._add_question_object(question_obj):
                    imported_count += 1
        else:
            print(f"错误: 文件 '{source_file_path}' 的根结构必须是JSON对象或JSON数组。")
            return 0

        # 仅在成功导入至少一个题目后才保存
        if imported_count > 0:
            self._save_database()

        return imported_count

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        for q in self.questions:
            if q.get('questionId') == question_id:
                return q
        return None

    def get_questions_by_kpid(self, kpid: str) -> List[Dict[str, Any]]:
        matched_questions = []
        for q in self.questions:
            if kpid in q.get('metadata', {}).get('knowledgePointIds', []):
                matched_questions.append(q)
        return matched_questions

    def get_total_questions(self) -> int:
        return len(self.questions)