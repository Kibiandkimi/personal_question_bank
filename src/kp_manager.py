import json
import os
from typing import List, Dict, Any, Optional
from collections import defaultdict

class KnowledgePointManager:
    """
    知识点管理器类 (重构版)。
    支持多种导入模式。
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.kps: List[Dict[str, Any]] = []
        self.kp_index: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.kps = json.loads(content) if content else []
        except json.JSONDecodeError:
            raise ValueError(f"无法解析 JSON 文件: {self.db_path}")

        self._build_index()

    def _build_index(self):
        self.kp_index = {kp['kpid']: kp for kp in self.kps}

    def _save_database(self):
        """将当前内存中的知识点数据写入到 JSON 文件中。"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.kps, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise IOError(f"写入数据库文件 '{self.db_path}' 失败: {e}")

    def get_kp_by_id(self, kpid: str) -> Optional[Dict[str, Any]]:
        return self.kp_index.get(kpid)

    def print_outline(self):
        print("===== 知识点大纲 (树状图) =====")
        if not self.kps:
            print("知识点库为空。")
            print("================================")
            return

        children_map = defaultdict(list)
        for kp in self.kps:
            children_map[kp.get('parentId')].append(kp)

        def _print_recursive(parent_id: Optional[str], prefix: str):
            children = sorted(children_map.get(parent_id, []), key=lambda x: x['kpid'])
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└─ " if is_last else "├─ "
                display_text = child.get('title') or child.get('content', '')
                short_text = (display_text[:40] + '...') if len(display_text) > 40 else display_text
                print(f"{prefix}{connector}[{child.get('type', 'N/A')}] {child['kpid']} - {short_text}")
                new_prefix = prefix + ("    " if is_last else "│   ")
                _print_recursive(child['kpid'], new_prefix)

        _print_recursive(None, "")
        print("================================")

    def get_ancestry(self, kpid: str) -> List[Dict[str, Any]]:
        ancestry = []
        current_kp = self.get_kp_by_id(kpid)
        while current_kp:
            ancestry.append(current_kp)
            parent_id = current_kp.get('parentId')
            if parent_id:
                current_kp = self.get_kp_by_id(parent_id)
            else:
                break
        return list(reversed(ancestry))

    # --- 重构后的导入方法 ---
    def import_from_file(self, filepath: str, mode: str = 'merge') -> Dict[str, int]:
        """
        从JSON文件导入知识点体系，支持多种导入模式。

        Args:
            filepath: 新知识点体系的JSON文件路径。
            mode: 导入模式 ('replace', 'append', 'merge')。

        Returns:
            一个包含操作摘要的字典, e.g., {'added': 10, 'updated': 5, 'skipped': 3, 'total': 28}
        """
        # 1. 读取并验证新文件
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                new_kps = json.load(f)
        except Exception as e:
            raise ValueError(f"读取或解析文件 '{filepath}' 失败: {e}")

        if not isinstance(new_kps, list):
            raise TypeError("导入失败: 文件内容必须是一个JSON对象列表。")

        summary = {'added': 0, 'updated': 0, 'skipped': 0}

        # 2. 根据模式执行逻辑
        if mode == 'replace':
            self.kps = new_kps
            summary['added'] = len(new_kps)

        elif mode in ['append', 'merge']:
            # 为了效率，预先构建现有kpid的集合和索引映射
            existing_kpid_set = {kp['kpid'] for kp in self.kps}
            kpid_to_index_map = {kp['kpid']: i for i, kp in enumerate(self.kps)}

            for new_kp in new_kps:
                kpid = new_kp.get('kpid')
                if not kpid:
                    summary['skipped'] += 1
                    continue

                if kpid in existing_kpid_set:
                    if mode == 'append':
                        summary['skipped'] += 1
                    else: # mode == 'merge'
                        idx = kpid_to_index_map[kpid]
                        self.kps[idx] = new_kp
                        summary['updated'] += 1
                else:
                    self.kps.append(new_kp)
                    summary['added'] += 1
        else:
            raise ValueError(f"未知的导入模式: '{mode}'")

        # 3. 保存并重建索引
        self._save_database()
        self._build_index()

        summary['total'] = len(self.kps)
        return summary

# --- 以下是用于测试的代码 ---
if __name__ == "__main__":
    # --- 测试设置 ---
    BASE_DATA = [
        {"kpid": "BIO-01", "title": "生物知识点1 (原始)", "parentId": "BIO"},
        {"kpid": "BIO-02", "title": "生物知识点2", "parentId": "BIO"},
    ]
    IMPORT_DATA = [
        {"kpid": "BIO-01", "title": "生物知识点1 (已更新)", "parentId": "BIO"}, #  更新
        {"kpid": "BIO-03", "title": "生物知识点3 (新增)", "parentId": "BIO"}, #  新增
    ]
    TEST_DB_PATH = "temp_test_db.json"
    TEST_IMPORT_PATH = "temp_test_import.json"

    def setup_files():
        with open(TEST_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(BASE_DATA, f)
        with open(TEST_IMPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(IMPORT_DATA, f)

    def cleanup_files():
        if os.path.exists(TEST_DB_PATH): os.remove(TEST_DB_PATH)
        if os.path.exists(TEST_IMPORT_PATH): os.remove(TEST_IMPORT_PATH)

    # --- 测试函数 ---
    def test_replace_mode():
        print("\n--- 测试 'replace' 模式 ---")
        setup_files()
        manager = KnowledgePointManager(TEST_DB_PATH)
        summary = manager.import_from_file(TEST_IMPORT_PATH, mode='replace')

        assert summary['added'] == 2
        assert summary['updated'] == 0
        assert summary['skipped'] == 0
        assert summary['total'] == 2
        assert manager.get_kp_by_id("BIO-02") is None # 旧数据已被删除
        print("✅ 'replace' 模式测试通过！")
        cleanup_files()

    def test_append_mode():
        print("\n--- 测试 'append' 模式 ---")
        setup_files()
        manager = KnowledgePointManager(TEST_DB_PATH)
        summary = manager.import_from_file(TEST_IMPORT_PATH, mode='append')

        assert summary['added'] == 1      # BIO-03
        assert summary['updated'] == 0
        assert summary['skipped'] == 1    # BIO-01
        assert summary['total'] == 3      # BIO-01, BIO-02, BIO-03
        assert manager.get_kp_by_id("BIO-01")['title'] == "生物知识点1 (原始)" # 未被更新
        print("✅ 'append' 模式测试通过！")
        cleanup_files()

    def test_merge_mode():
        print("\n--- 测试 'merge' 模式 ---")
        setup_files()
        manager = KnowledgePointManager(TEST_DB_PATH)
        summary = manager.import_from_file(TEST_IMPORT_PATH, mode='merge')

        assert summary['added'] == 1      # BIO-03
        assert summary['updated'] == 1    # BIO-01
        assert summary['skipped'] == 0
        assert summary['total'] == 3      # BIO-01, BIO-02, BIO-03
        assert manager.get_kp_by_id("BIO-01")['title'] == "生物知识点1 (已更新)" # 已被更新
        print("✅ 'merge' 模式测试通过！")
        cleanup_files()

    # --- 运行所有测试 ---
    try:
        test_replace_mode()
        test_append_mode()
        test_merge_mode()
        print("\n🎉 所有测试用例均已通过！")
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
    finally:
        cleanup_files()