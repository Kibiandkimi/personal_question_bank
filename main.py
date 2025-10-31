import click
import os
import sys
import json
from src.kp_manager import KnowledgePointManager
from src.question_manager import QuestionManager

# --- 配置与初始化 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KP_FILE = os.path.join(BASE_DIR, "data", "knowledge_points.json")
Q_DB_FILE = os.path.join(BASE_DIR, "data", "questions.json")

try:
    kp_manager = KnowledgePointManager(KP_FILE)
    question_manager = QuestionManager(Q_DB_FILE)
except Exception as e:
    click.secho(f"❌ 系统初始化失败: {e}", fg='red', err=True)
    sys.exit(1)

# --- CLI 命令定义 ---
@click.group()
def cli():
    """
    AI驱动的个人题库系统 CLI。
    使用 'question' 和 'kp' 子命令来操作题库和知识点。
    """
    pass

# --- 1.2.1 创建 'question' 命令组 ---
@cli.group()
def question():
    """管理和查询题库中的题目。"""
    pass

# --- 1.2.2 创建 'kp' 命令组 ---
@cli.group()
def kp():
    """管理和查询知识点体系。"""
    pass

# --- 1.2.3 实现 'question find' 命令 ---
@question.command(name='find')
@click.option('--text', help='在题干中搜索指定文本。')
@click.option('--kpid', help='根据知识点ID进行筛选。')
@click.option('--source', help='根据题目来源进行筛选。')
@click.option('--qtype', '--question-type', 'question_type', help="根据题目类型筛选 (e.g., SINGLE_CHOICE)。")
@click.option('--wrong', 'is_wrong', is_flag=True, help='只显示被标记为错题的题目。')
def find_questions(text, kpid, source, question_type, is_wrong):
    """
    根据一个或多个条件查找题目。
    """
    # 如果 is_wrong flag 未被使用, 它的值是 False, 但我们想把它当作 "不筛选"
    # 所以我们只在它为 True 时才传递它
    is_wrong_filter = True if is_wrong else None

    results = question_manager.find_questions(
        text_in_stem=text,
        kpid=kpid,
        source=source,
        is_wrong=is_wrong_filter,
        question_type=question_type
    )

    if not results:
        click.secho("🟡 未找到符合条件的题目。", fg='yellow')
        return

    click.secho(f"✅ 找到 {len(results)} 道相关题目:", fg='green')

    # 1.2.6 格式化输出
    # 打印表头
    click.echo("-" * 100)
    click.echo(f"{'Question ID':<38}{'Type':<20}{'Stem'}")
    click.echo("-" * 100)

    for q in results:
        q_id = q.get('questionId', 'N/A')
        # 如果 questionType 为空 (例如母题), 则显示 structureType
        q_type = q.get('questionType') or q.get('structureType', 'N/A')
        stem = q.get('stem', '')

        # 截断过长的题干
        short_stem = (stem[:50] + '...') if len(stem) > 50 else stem

        click.echo(f"{q_id:<38}{q_type:<20}{short_stem}")

    click.echo("-" * 100)
    click.echo("提示: 使用 'question show <ID>' 查看题目详情。")


# --- 将旧命令迁移到新的命令组下 ---

@question.command(name='show')
@click.argument('question_id')
def show_question(question_id):
    """显示指定题目的完整信息及其上下文。"""
    context = question_manager.get_full_question_context(question_id)
    target_question = context.get('target')

    if not target_question:
        click.secho(f"❌ 未找到 ID 为 '{question_id}' 的题目。", fg='red')
        return

    if context.get('parent'):
        parent = context['parent']
        click.secho("\n--- PARENT MATERIAL --------------------------", fg='yellow')
        click.echo(f"Parent ID: {parent.get('questionId')}")
        click.echo(f"Material: {parent.get('stem')}")
        click.secho("------------------------------------------\n", fg='yellow')

    click.secho(f"--- TARGET QUESTION (ID: {target_question.get('questionId')}) ---", fg='cyan')
    formatted_json = json.dumps(target_question, ensure_ascii=False, indent=2)
    click.echo(formatted_json)
    click.secho("--------------------------------------------------", fg='cyan')

    if context.get('children'):
        children = context['children']
        click.secho("\n--- CHILDREN OF THIS QUESTION ----------------", fg='yellow')
        for child in children:
            click.echo(f"  - Child ID: {child.get('questionId')}")
            click.echo(f"    Stem: {child.get('stem')}")
        click.secho("------------------------------------------", fg='yellow')

@question.command(name='import')
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def import_question(filepath):
    """导入单个或批量的题目JSON文件到题库。"""
    click.echo(f"正在从 '{os.path.basename(filepath)}' 导入题目...")
    imported_results = question_manager.import_question_from_file(filepath)
    imported_count = len(imported_results)

    if imported_count > 0:
        click.secho(f"✅ 成功导入 {imported_count} 道题目！", fg='green')
        if 1 <= imported_count <= 5:
            click.echo("   新题目 ID 列表:")
            for result in imported_results:
                click.echo(f"     - {result.get('questionId')}")
        click.echo(f"   当前题库总数: {question_manager.get_total_questions()}")
    else:
        click.secho(f"❌ 导入失败。请检查文件内容和格式。", fg='red')

@kp.command(name='outline')
def outline_kps():
    """显示完整的知识点大纲树状图。"""
    kp_manager.print_outline()

@kp.command(name='import')
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    '--mode',
    type=click.Choice(['replace', 'append', 'merge'], case_sensitive=False),
    default='merge',
    help='Import mode: replace, append, or merge.'
)
def import_kps(filepath, mode):
    """从文件导入知识点体系，支持多种导入模式。"""
    try:
        if mode == 'replace':
            click.confirm('⚠️ 警告: "replace"模式将完全覆盖你当前的知识点体系。确定要继续吗?', abort=True)

        click.echo(f"🚀 正在以 '{mode}' 模式从 '{os.path.basename(filepath)}' 导入...")
        summary = kp_manager.import_from_file(filepath, mode=mode)

        click.secho("\n✅ 导入完成！", fg='green')
        click.echo("--- Import Summary ---")
        click.echo(f"  - 新增条目: {summary['added']}")
        click.echo(f"  - 更新条目: {summary['updated']}")
        click.echo(f"  - 跳过条目: {summary['skipped']}")
        click.echo("----------------------")
        click.echo(f"  - 数据库总条目: {summary['total']}")

    except click.exceptions.Abort:
        click.secho("操作已取消。", fg='yellow')
    except Exception as e:
        click.secho(f"❌ 导入失败: {e}", fg='red')

if __name__ == '__main__':
    cli()