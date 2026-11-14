# src/nova_forge/core/templates/__init__.py

from .tmpl_config import (
    DEFAULT_GITHUB_USER,
    DEFAULT_REAL_NAME,
    DEFAULT_DESC_EN,
    DEFAULT_DESC_ZH,
    DEFAULT_DEPS,
    CB,
)
from .tmpl_pyproject import PYPROJECT_TMPL
from .tmpl_license import LICENSE_TMPL
from .tmpl_readme import README_EN_TMPL, README_ZH_TMPL
from .tmpl_python_files import CHANGELOG_TMPL, INIT_PY_TMPL, GITIGNORE_TMPL
from .tmpl_workflow import WORKFLOW_TMPL
from .tmpl_how_to_publish import HOW_TO_PUBLISH_TMPL
from .tmpl_mobile import MOBILE_MAIN_PY_TMPL, MOBILE_MAIN_QML_TMPL

__all__ = [
    "DEFAULT_GITHUB_USER",
    "DEFAULT_REAL_NAME",
    "DEFAULT_DESC_EN",
    "DEFAULT_DESC_ZH",
    "DEFAULT_DEPS",
    "CB",
    "PYPROJECT_TMPL",
    "LICENSE_TMPL",
    "README_EN_TMPL",
    "README_ZH_TMPL",
    "CHANGELOG_TMPL",
    "INIT_PY_TMPL",
    "GITIGNORE_TMPL",
    "WORKFLOW_TMPL",
    "HOW_TO_PUBLISH_TMPL",
    "MOBILE_MAIN_PY_TMPL",
    "MOBILE_MAIN_QML_TMPL",
]
