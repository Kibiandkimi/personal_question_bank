import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class QuestionManager:
    """
    题目管理器类 (架构升级版)。
    原生支持层级题目结构 (母题/子题)。
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

        if 'structureType' not in question_data or 'parentId' not in question_data:
            print(f"警告: 导入的题目 (ID: {question_data.get('questionId', 'N/A')}) 缺少层级字段。将自动设置为独立的原子题。")
            question_data.setdefault('structureType', 'ATOMIC')
            question_data.setdefault('parentId', None)

        question_data['questionId'] = str(uuid.uuid4())
        question_data['importTimestampUTC'] = datetime.utcnow().isoformat()
        self.questions.append(question_data)
        return question_data

    def import_question_from_file(self, source_file_path: str) -> List[Dict[str, Any]]:
        """
        从 JSON 文件导入题目，返回所有成功导入的题目对象列表。
        """
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"错误: 无法读取或解析文件 '{source_file_path}': {e}")
            return []

        imported_questions = []
        if isinstance(data, dict):
            new_question = self._add_question_object(data)
            if new_question:
                imported_questions.append(new_question)
        elif isinstance(data, list):
            for question_obj in data:
                new_question = self._add_question_object(question_obj)
                if new_question:
                    imported_questions.append(new_question)

        if imported_questions:
            self._save_database()

        return imported_questions

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        for q in self.questions:
            if q.get('questionId') == question_id:
                return q
        return None

    def get_total_questions(self) -> int:
        return len(self.questions)

    def get_children(self, parent_id: str) -> List[Dict[str, Any]]:
        return [q for q in self.questions if q.get('parentId') == parent_id]

    def get_full_question_context(self, question_id: str) -> Dict[str, Any]:
        """
        获取指定题目的完整上下文（本身、母题、子题）。

        Args:
            question_id: 任意一个题目的 questionId。

        Returns:
            一个包含上下文信息的字典: {'target': ..., 'parent': ..., 'children': ...}
        """
        context = {
            "target": None,
            "parent": None,
            "children": []
        }

        target_question = self.get_question_by_id(question_id)
        if not target_question:
            return context

        context['target'] = target_question
        parent_id = target_question.get('parentId')
        if parent_id:
            context['parent'] = self.get_question_by_id(parent_id)
        if target_question.get('structureType') == 'COMPOSITE':
            context['children'] = self.get_children(question_id)

        return context