"""一键发布 AstroNova v1.0.0 — 推代码 + 创建 GitHub Release"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=ROOT):
    print(f"$ {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)


def main():
    version = "v1.0.0"

    print("=" * 60)
    print(f"发布 AstroNova {version}")
    print("=" * 60)

    # 1. 推送代码
    print("\n[1/4] 推送到 GitHub...")
    run("git push origin master")

    # 2. 打标签
    print(f"\n[2/4] 创建标签 {version}...")
    run(f"git tag -a {version} -m 'AstroNova {version}'")
    run(f"git push origin {version}")

    # 3. 创建 Release 并上传安装包 + latest.yml（自动更新用）
    print("\n[3/4] 创建 GitHub Release...")
    run(f"gh release create {version} "
        f"dist/AstroNova-Setup-{version[1:]}.exe "
        f"dist/AstroNova-Setup-{version[1:]}.exe.blockmap "
        f"dist/latest.yml "
        f"--title 'AstroNova {version}' "
        f"--notes '首次公开发布。详见 README。'")

    # 4. 验证
    print("\n[4/4] 验证 Release...")
    run(f"gh release view {version}")

    print(f"\n{'=' * 60}")
    print(f"发布完成！https://github.com/SiriusFzh/astro-nova/releases/tag/{version}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
