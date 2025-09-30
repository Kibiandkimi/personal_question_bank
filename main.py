import click
import os
import sys
import json
# 从 src 包中导入我们编写的管理器类
from src.kp_manager import KnowledgePointManager
from src.question_manager import QuestionManager

# --- 配置与初始化 ---

# 定义数据文件的路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KP_FILE = os.path.join(BASE_DIR, "data", "knowledge_points.json")
Q_DB_FILE = os.path.join(BASE_DIR, "data", "questions.json")

# 初始化管理器实例
# 我们在这里进行全局初始化，以便所有命令都能使用它们
try:
    kp_manager = KnowledgePointManager(KP_FILE)
    question_manager = QuestionManager(Q_DB_FILE)
except Exception as e:
    # 使用 click.secho 打印带颜色的错误信息
    click.secho(f"❌ 系统初始化失败: {e}", fg='red', err=True)
    click.secho("请检查 data/ 目录下的配置文件是否存在。", fg='red', err=True)
    sys.exit(1)

# --- CLI 命令定义 ---

@click.group()
def cli():
    """
    AI驱动的个人题库系统 CLI (命令行界面)。
    这是第一阶段 (MVP) 的主入口。
    """
    pass

@cli.command()
def outline():
    """显示完整的知识点大纲树状图。"""
    kp_manager.print_outline()

@cli.command(name='import')
@click.argument('filepath', type=click.Path(exists=True))
def import_question(filepath):
    """
    导入单个题目JSON文件到题库。

    FILEPATH: 待导入的题目JSON文件的路径。
    """
    click.echo(f"正在从 '{filepath}' 导入题目...")
    result = question_manager.import_question_from_file(filepath)

    if result:
        new_id = result.get('questionId')
        click.secho(f"✅ 导入成功！", fg='green')
        click.echo(f"   新题目 ID: {new_id}")
        click.echo(f"   当前题库总数: {question_manager.get_total_questions()}")
    else:
        click.secho(f"❌ 导入失败，请检查文件格式。", fg='red')

@cli.command()
@click.option('--kpid', required=True, help='要查找的知识点编码 (KPID)。')
def find(kpid):
    """根据知识点ID (KPID) 查找所有关联的题目。"""
    # 1. 首先检查这个 KPID 是否存在 (可选，但能提供更好的用户体验)
    kp_info = kp_manager.get_kp_by_id(kpid)
    if not kp_info:
        click.secho(f"⚠️ 警告: 知识点编码 '{kpid}' 在知识点库中不存在。", fg='yellow')
    else:
        kp_statement = kp_info.get("原子知识点 (陈述句)", "")
        click.echo(f"🔍 正在查找关联知识点: [{kpid}] {kp_statement}")

    # 2. 在题库中查找
    questions = question_manager.get_questions_by_kpid(kpid)

    if questions:
        click.secho(f"✅ 找到 {len(questions)} 道相关题目:", fg='green')
        for q in questions:
            q_id = q.get('questionId')
            stem = q.get('stem', '')
            # 只显示题干的前50个字符
            short_stem = (stem[:50] + '...') if len(stem) > 50 else stem
            click.echo(f"   - ID: {q_id}")
            click.echo(f"     题干: {short_stem}")
        click.echo("\n提示: 使用 'python main.py show <ID>' 查看题目详情。")
    else:
        click.secho(f"未找到与 KPID '{kpid}' 关联的题目。", fg='yellow')

@cli.command()
@click.argument('question_id')
def show(question_id):
    """
    显示指定题目的完整详细信息。

    QUESTION_ID: 题目的唯一ID (UUID)。
    """
    question = question_manager.get_question_by_id(question_id)

    if question:
        click.secho(f"📖 题目详情 ({question_id}):", fg='cyan')
        # 使用 json.dumps 漂亮地打印整个字典
        formatted_json = json.dumps(question, ensure_ascii=False, indent=2)
        click.echo(formatted_json)
    else:
        click.secho(f"❌ 未找到 ID 为 '{question_id}' 的题目。", fg='red')

if __name__ == '__main__':
    cli()