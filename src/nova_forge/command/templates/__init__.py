# src/nova_forge/command/templates/__init__.py

from .tmpl_config import (
    CB,
    DEFAULT_DEPS,
    DEFAULT_DESC_EN,
    DEFAULT_DESC_ZH,
    DEFAULT_GITHUB_USER,
    DEFAULT_REAL_NAME,
)
from .tmpl_how_to_publish import HOW_TO_PUBLISH_TMPL
from .tmpl_license import LICENSE_TMPL
from .tmpl_mobile import MOBILE_MAIN_PY_TMPL, MOBILE_MAIN_QML_TMPL
from .tmpl_pyproject import PYPROJECT_TMPL
from .tmpl_python_files import CHANGELOG_TMPL, GITIGNORE_TMPL, INIT_PY_TMPL
from .tmpl_readme import README_EN_TMPL, README_ZH_TMPL
from .tmpl_workflow import WORKFLOW_TMPL

__all__ = [
    "CB",
    "CHANGELOG_TMPL",
    "DEFAULT_DEPS",
    "DEFAULT_DESC_EN",
    "DEFAULT_DESC_ZH",
    "DEFAULT_GITHUB_USER",
    "DEFAULT_REAL_NAME",
    "GITIGNORE_TMPL",
    "HOW_TO_PUBLISH_TMPL",
    "INIT_PY_TMPL",
    "LICENSE_TMPL",
    "MOBILE_MAIN_PY_TMPL",
    "MOBILE_MAIN_QML_TMPL",
    "PYPROJECT_TMPL",
    "README_EN_TMPL",
    "README_ZH_TMPL",
    "WORKFLOW_TMPL",
]
