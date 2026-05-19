"""一键发布 AstroNova — 打标签触发 CI 自动构建 + 发布"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gh(cmd, cwd=ROOT):
    print(f"$ gh {cmd}")
    result = subprocess.run(f"gh {cmd}", shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    version = f"v{sys.argv[1]}" if len(sys.argv) > 1 else None
    if not version:
        print("Usage: python scripts/publish_release.py <version>")
        print("Example: python scripts/publish_release.py 1.0.1")
        sys.exit(1)

    print("=" * 60)
    print(f"发布 AstroNova {version}")
    print("=" * 60)
    print()
    print("这个脚本会:")
    print(f"  1. 在 GitHub 上创建 tag {version}")
    print("  2. GitHub Actions CI 会自动构建 Windows + macOS 安装包")
    print("  3. CI 完成后自动创建 Release 并上传 artifacts")
    print()

    # 确认
    confirm = input(f"确认发布 {version}？(y/N) ").strip().lower()
    if confirm != "y":
        print("已取消")
        sys.exit(0)

    # 1. 检查是否在 master/main 分支
    branch = gh("branch --show-current")
    if branch not in ("master", "main"):
        print(f"警告: 当前在 {branch} 分支，建议从 master/main 发布")
        sure = input("继续？(y/N) ").strip().lower()
        if sure != "y":
            print("已取消")
            sys.exit(0)

    # 2. 检查本地是否有未提交修改
    status = gh("status --porcelain")
    if status:
        print("警告: 有未提交的修改：")
        print(status)
        sure = input("继续发布？(y/N) ").strip().lower()
        if sure != "y":
            print("已取消")
            sys.exit(0)

    # 3. 通过 GitHub API 创建 tag 和 release（不走 git push）
    print(f"\n[1/2] 创建 tag {version}...")
    gh(f'api repos/SiriusFzh/astro-nova/git/refs -f ref=refs/tags/{version} -f sha=$(gh api repos/SiriusFzh/astro-nova/git/refs/heads/{branch} --jq .object.sha)')
    print(f"  ✓ tag {version} 已创建")

    # 4. CI 会自动触发 build + release
    print(f"\n[2/2] CI 已触发！")
    print(f"  查看进度: https://github.com/SiriusFzh/astro-nova/actions")
    print(f"  发布后:    https://github.com/SiriusFzh/astro-nova/releases/tag/{version}")
    print()

    print(f"{'=' * 60}")
    print(f"发布流程已启动！等待 CI 完成...")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
