import json
import os
from typing import Dict, Any, Optional

class KnowledgePointManager:
    """
    知识点管理器类。
    负责加载知识点数据，并提供查询和展示功能。
    """

    def __init__(self, data_file_path: str):
        """
        初始化管理器。

        Args:
            data_file_path: knowledge_points.json 文件的路径。
        """
        self.data_file_path = data_file_path
        self.kp_data: Dict[str, Any] = {}
        # 核心索引：用于通过 KPID 快速查找原子知识点
        self.kp_index: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        """
        从 JSON 文件加载数据，并构建 KPID 索引。
        这是一个内部方法，在初始化时自动调用。
        """
        if not os.path.exists(self.data_file_path):
            raise FileNotFoundError(f"知识点数据文件未找到: {self.data_file_path}")

        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.kp_data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"无法解析 JSON 文件: {self.data_file_path}，请检查文件格式。")

        # 加载数据后，立即构建索引
        self._build_index()

    def _build_index(self):
        """
        遍历嵌套的知识点数据结构，构建 KPID 到原子知识点的映射索引。
        """
        self.kp_index = {} # 重置索引

        # 遍历 章 (Chapter)
        for chapter_name, sections in self.kp_data.items():
            # 遍历 节 (Section)
            for section_name, topics in sections.items():
                # 遍历 主题 (Topic)
                for topic in topics:
                    atomic_kps = topic.get("原子知识点列表", [])
                    # 遍历 原子知识点 (Atomic KP)
                    for akp in atomic_kps:
                        kpid = akp.get("知识点编码 (KPID)")
                        if kpid:
                            # 将原子知识点存入索引，并附加上层级信息，方便后续使用
                            akp_with_context = akp.copy()
                            akp_with_context["_context"] = {
                                "chapter": chapter_name,
                                "section": section_name,
                                "topic": topic.get("知识点主题")
                            }
                            self.kp_index[kpid] = akp_with_context

    def get_kp_by_id(self, kpid: str) -> Optional[Dict[str, Any]]:
        """
        通过 KPID 查找对应的原子知识点详细信息。

        Args:
            kpid: 知识点编码，例如 "BIO-B1-C02-S01-T01-A01"

        Returns:
            包含原子知识点信息的字典，如果未找到则返回 None。
        """
        return self.kp_index.get(kpid)

    def print_outline(self):
        """
        以树状结构打印出整个知识点大纲。
        """
        print("===== 知识点大纲 =====")
        for chapter_name, sections in self.kp_data.items():
            print(f"📖 {chapter_name}")
            for section_name, topics in sections.items():
                print(f"  └─ 🔖 {section_name}")
                for topic in topics:
                    topic_name = topic.get("知识点主题", "未命名主题")
                    print(f"      └─ 💡 {topic_name}")
                    atomic_kps = topic.get("原子知识点列表", [])
                    for akp in atomic_kps:
                        kpid = akp.get("知识点编码 (KPID)", "No ID")
                        statement = akp.get("原子知识点 (陈述句)", "")
                        # 截取过长的陈述句以便展示
                        short_statement = (statement[:30] + '...') if len(statement) > 30 else statement
                        print(f"          └─ [{kpid}] {short_statement}")
        print("======================")

# --- 以下是用于测试的代码 ---
if __name__ == "__main__":
    # 定义数据文件的相对路径
    # 注意：我们假设从项目根目录运行此脚本
    DATA_FILE = os.path.join("data", "knowledge_points.json")

    print(f"正在尝试加载数据文件: {DATA_FILE}")

    try:
        # 1. 初始化管理器
        kp_manager = KnowledgePointManager(DATA_FILE)
        print("✅ 知识点管理器初始化成功！")

        # 2. 测试打印大纲
        print("\n--- 测试功能 1: 打印大纲 ---")
        kp_manager.print_outline()

        # 3. 测试通过 KPID 查找
        print("\n--- 测试功能 2: 通过 KPID 查找 ---")
        test_kpid = "BIO-B1-C02-S01-T01-A01"
        print(f"正在查找 KPID: {test_kpid}")
        kp = kp_manager.get_kp_by_id(test_kpid)

        if kp:
            print("✅ 找到知识点:")
            # 使用 json.dumps 漂亮地打印字典
            print(json.dumps(kp, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 未找到 KPID 为 {test_kpid} 的知识点。")

        # 4. 测试查找一个不存在的 KPID
        print("\n--- 测试功能 3: 查找不存在的 KPID ---")
        test_kpid_not_exist = "BIO-XXXXX"
        print(f"正在查找 KPID: {test_kpid_not_exist}")
        kp_not_exist = kp_manager.get_kp_by_id(test_kpid_not_exist)
        if kp_not_exist:
             print("❌ 错误：不应该找到这个知识点。")
        else:
             print(f"✅ 正确：未找到 KPID 为 {test_kpid_not_exist} 的知识点。")


    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        print("请确保你是在项目根目录 'personal_question_bank' 下运行此脚本。")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")