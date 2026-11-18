# src/nova_forge/core/tmpl_how_to_publish.py
from .tmpl_config import CB

HOW_TO_PUBLISH_TMPL = """# 🚀 How to Publish to PyPI (Trusted Publishing)

本项目已自动配置了 **OIDC Trusted Publishing**（免密安全发版）。
你不需要在 GitHub 里存任何密码（API Token），只需在 PyPI 网页端完成一次绑定:

1. 登录 PyPI，访问 [Publishing 设置页](https://pypi.org/manage/account/publishing/)。
2. 找到 **"Add a new pending publisher"** 并填写以下信息（请严格区分大小写）:
   - **PyPI Project Name**: `$PROJECT_NAME`
   - **Owner**: `$GITHUB_USER`
   - **Repository name**: `$REPO_NAME`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
3. 点击保存。

完成上述配置后，在本地打上 Git Tag 并推送，或者直接在 GitHub Actions 页面手动触发，即可全自动发版:

${CB}bash
git tag v0.1.0
git push origin v0.1.0
${CB}
"""
