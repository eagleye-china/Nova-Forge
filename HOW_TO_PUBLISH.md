# 🚀 How to Publish to PyPI (Trusted Publishing)

本项目已自动配置了 **OIDC Trusted Publishing**（免密安全发版）。
你不需要在 GitHub 里存任何密码（API Token），只需在 PyPI 网页端完成一次绑定：

1. 登录 PyPI，访问 [Publishing 设置页](https://pypi.org/manage/account/publishing/)。
2. 找到 **"Add a new pending publisher"** 并填写以下信息（请严格区分大小写）：
   - **PyPI Project Name**: `nova-forge`
   - **Owner**: `eagleye-china`
   - **Repository name**: `Nova-Forge`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
3. 点击保存。

完成上述配置后，在本地打上 Git Tag 并推送，即可触发 GitHub Actions 全自动发版：

```bash
git tag v0.2.0c
git push origin v0.2.0c