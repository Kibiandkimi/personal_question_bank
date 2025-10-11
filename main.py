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
    """AI驱动的个人题库系统 CLI。"""
    pass

@cli.command()
def outline():
    """显示完整的知识点大纲树状图。"""
    kp_manager.print_outline()

# --- 升级后的 import-kps 命令 ---
@cli.command(name='import-kps')
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    '--mode',
    type=click.Choice(['replace', 'append', 'merge'], case_sensitive=False),
    default='merge',
    help=(
        'Import mode: "replace" (overwrite all), "append" (add new only), '
        '"merge" (default: add new and update existing).'
    )
)
def import_kps(filepath, mode):
    """
    从文件导入知识点体系，支持多种导入模式。
    """
    try:
        # 仅在 replace 模式下要求二次确认
        if mode == 'replace':
            click.confirm(
                '⚠️ 警告: "replace"模式将完全覆盖你当前的知识点体系。确定要继续吗?',
                abort=True
            )

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


@cli.command(name='import')
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def import_question(filepath):
    """
    导入单个或批量的题目JSON文件到题库。

    FILEPATH: 待导入的题目JSON文件的路径。
    文件内容可以是单个题目对象，也可以是题目对象组成的数组。
    """
    click.echo(f"正在从 '{os.path.basename(filepath)}' 导入题目...")
    imported_count = question_manager.import_question_from_file(filepath)
    if imported_count > 0:
        click.secho(f"✅ 成功导入 {imported_count} 道题目！", fg='green')
        click.echo(f"   当前题库总数: {question_manager.get_total_questions()}")
    else:
        click.secho(f"❌ 导入失败。请检查文件内容和格式。", fg='red')

# (find 和 show 命令无变化)
@cli.command()
@click.option('--kpid', required=True, help='要查找的知识点编码 (KPID)。')
def find(kpid):
    """根据知识点ID (KPID) 查找所有关联的题目。"""
    kp_info = kp_manager.get_kp_by_id(kpid)
    if not kp_info:
        click.secho(f"⚠️ 警告: 知识点编码 '{kpid}' 在知识点库中不存在。", fg='yellow')
    else:
        display_text = kp_info.get('title') or kp_info.get('content', '')
        click.echo(f"🔍 正在查找关联知识点: [{kpid}] {display_text}")

    questions = question_manager.get_questions_by_kpid(kpid)
    if questions:
        click.secho(f"✅ 找到 {len(questions)} 道相关题目:", fg='green')
        for q in questions:
            q_id = q.get('questionId')
            stem = q.get('stem', '')
            short_stem = (stem[:50] + '...') if len(stem) > 50 else stem
            click.echo(f"   - ID: {q_id}")
            click.echo(f"     题干: {short_stem}")
        click.echo("\n提示: 使用 'python main.py show <ID>' 查看题目详情。")
    else:
        click.secho(f"未找到与 KPID '{kpid}' 关联的题目。", fg='yellow')

@cli.command()
@click.argument('question_id')
def show(question_id):
    """显示指定题目的完整详细信息。"""
    question = question_manager.get_question_by_id(question_id)
    if question:
        click.secho(f"📖 题目详情 ({question_id}):", fg='cyan')
        formatted_json = json.dumps(question, ensure_ascii=False, indent=2)
        click.echo(formatted_json)
    else:
        click.secho(f"❌ 未找到 ID 为 '{question_id}' 的题目。", fg='red')

if __name__ == '__main__':
    cli()