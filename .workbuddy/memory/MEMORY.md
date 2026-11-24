# nova-forge 项目长期约定

## 工作区边界（2026-11-24 复诊更新，最重要）
- **当前唯一有效工作区 = D 盘** `D:/Porjects/PyCharm/PySide6/Nova/nova-forge`。
  实测 2026-11-24：conda 环境 `pyside6_nova` 的 nova-forge 是 editable 安装，
  `Editable project location` 指向此 D 盘路径；用户报错 traceback 也是此路径。
- **原记录已作废**：旧笔记称"C 盘 `C:/Porjects/PyCharm/PySide6/Nova/nova-forge` 是唯一权威、
  D 盘废弃"——复诊确认 **C 盘该路径已不存在**（环境/磁盘调整后不再有）。旧的
  `D:/MyProjects/PyCharm/Project_Nova/Nova-Forge` 废弃说法也一并作废。
- 结论：改代码前先 `python -c "import nova_forge; print(nova_forge.__file__)"` 确认 editable 指向，
  以实际指向为准，不要盲信旧笔记的盘符。

## 职责边界（用户 2026-11-23 明确）
- GitHub / PyPI 的推送、打 tag、上传发布一律归用户本人；小诺只负责命令本身正常运行与稳定健壮。
- 发布动作（git push / tag / PyPI upload）不执行，除非用户另行明确授权。
- 可做的：改命令代码、跑测试、只读检查、构建验证（不上传）。

## 交付纪律
- 称呼用户为"伙伴"；助手名小诺 / Nova（欧冶子铸剑、小诺守炉）。
- 任何改动后先跑 `python -m unittest discover -s tests -v` 全绿再交付。
- 改动文件按 D-008 规范更新首行路径与次行日期时间。
- 用户偏好：绝不接受 IDE 红/绿波浪线；检查配置已关 SpellChecking / PyPep8 / PyPackageRequirements，需重启 PyCharm 才生效。
- Git：不擅自提交、不推送。

## 版本与发布状态
- pyproject 版本 0.4.10；0.4.10 已上架 PyPI（2026-11-23 06:05），tag v0.4.10 已由用户推送。
- CHANGELOG 已同步到 0.4.10。
