# src/nova_forge/ui/icons_window.py
# 创建时间：星期二 2026-11-24 21:39
import re
import shutil
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..core.icons_logic import ResourceBuilderWorker

try:
    from src.svg_collector_pro.utils.generate_qrc import get_resources_base_dir
except ImportError:

    def get_resources_base_dir(root):
        return root / "resources"


def _detect_project_root() -> Path:
    """兼容源码目录与已安装环境：向上查找包含资源目录的项目根。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "resources").is_dir() and (parent / "assets").is_dir():
            return parent
    for parent in here.parents:
        if (parent / "resources").is_dir() or (parent / "assets").is_dir():
            return parent
    return Path.cwd()


class IconsWindow(QWidget):
    def __init__(self, log_bridge=None, parent=None):
        super().__init__(parent)
        self.log_bridge = log_bridge

        self.project_root = _detect_project_root()
        self.assets_base_dir = self.project_root / "assets"
        self.resources_base_dir = get_resources_base_dir(self.project_root)

        self.current_asset_folder = ""
        self.current_resource_folder = ""
        self.builder_worker = None

        self.setup_ui()
        self.refresh_asset_folders()
        self.refresh_resource_folders()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 【修改点】将 Qt.Orientation.Vertical 改为 Qt.Orientation.Horizontal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- 左侧部分:资产浏览区 ---
        assets_area = QWidget()
        assets_layout = QVBoxLayout(assets_area)
        assets_layout.setContentsMargins(0, 0, 5, 0)

        # 左侧的头部（因为变成了左右布局，搜索框太宽会挤压，所以要重构一下头部）
        assets_header_layout = QVBoxLayout()

        assets_title_row = QHBoxLayout()
        assets_title_row.addWidget(QLabel("📥 浏览资产目录:"))
        self.combo_assets = QComboBox()
        self.combo_assets.setStyleSheet("padding: 4px; min-width: 150px;")
        self.combo_assets.currentTextChanged.connect(self.on_asset_folder_changed)
        assets_title_row.addWidget(self.combo_assets)
        assets_title_row.addStretch()

        assets_header_layout.addLayout(assets_title_row)

        self.search_input_assets = QLineEdit()
        self.search_input_assets.setPlaceholderText("🔍 搜索资产图片...")
        self.search_input_assets.setClearButtonEnabled(True)
        self.search_input_assets.setStyleSheet("""
            QLineEdit { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; }
            QLineEdit:focus { border: 1px solid #0078D7; }
        """)
        self.search_input_assets.textChanged.connect(self.filter_assets)
        assets_header_layout.addWidget(self.search_input_assets)

        assets_layout.addLayout(assets_header_layout)

        self.icon_list = QListWidget()
        self.icon_list.setViewMode(QListView.ViewMode.IconMode)
        self.icon_list.setIconSize(QSize(64, 64))
        self.icon_list.setGridSize(QSize(110, 110))
        self.icon_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.icon_list.setWordWrap(True)
        self.icon_list.setMovement(QListView.Movement.Static)
        self.icon_list.setStyleSheet("""
            QListWidget { background-color: #CBE9CF; border: 1px solid #B2D3B6; border-radius: 4px; color: #1E361F; }
            QListWidget::item { border-radius: 6px; padding: 6px; }
            QListWidget::item:hover { background-color: #B8DCBD; }
            QListWidget::item:selected { background-color: #98C79F; color: #0A1A0B; }
        """)
        self.icon_list.itemDoubleClicked.connect(self.publish_single_icon)
        assets_layout.addWidget(self.icon_list)
        main_splitter.addWidget(assets_area)

        # --- 右侧部分:资源浏览区 ---
        resources_area = QWidget()
        resources_layout = QVBoxLayout(resources_area)
        resources_layout.setContentsMargins(5, 0, 0, 0)

        res_header_layout = QVBoxLayout()

        res_title_row = QHBoxLayout()
        res_title_row.addWidget(QLabel("📦 浏览资源目录:"))
        self.combo_resources = QComboBox()
        self.combo_resources.setStyleSheet("padding: 4px; min-width: 150px;")
        self.combo_resources.currentTextChanged.connect(self.on_resource_folder_changed)
        res_title_row.addWidget(self.combo_resources)
        res_title_row.addStretch()

        self.btn_refresh_res = QPushButton("🔄 刷新")
        self.btn_refresh_res.setStyleSheet("padding: 4px 8px;")
        self.btn_refresh_res.clicked.connect(self.refresh_resource_folders)
        res_title_row.addWidget(self.btn_refresh_res)

        self.btn_build = QPushButton("📝 更新 .qrc")
        self.btn_build.setStyleSheet(
            "padding: 4px 8px; background-color: #0078D7; color: white; border-radius: 4px; font-weight: bold;"
        )
        self.btn_build.clicked.connect(self.start_manual_build)
        res_title_row.addWidget(self.btn_build)

        res_header_layout.addLayout(res_title_row)

        self.search_input_resources = QLineEdit()
        self.search_input_resources.setPlaceholderText("🔍 搜索资源图片...")
        self.search_input_resources.setClearButtonEnabled(True)
        self.search_input_resources.setStyleSheet("""
            QLineEdit { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; }
            QLineEdit:focus { border: 1px solid #0078D7; }
        """)
        self.search_input_resources.textChanged.connect(self.filter_resources)
        res_header_layout.addWidget(self.search_input_resources)

        resources_layout.addLayout(res_header_layout)

        self.res_icon_list = QListWidget()
        self.res_icon_list.setViewMode(QListView.ViewMode.IconMode)
        self.res_icon_list.setIconSize(QSize(64, 64))
        self.res_icon_list.setGridSize(QSize(110, 110))
        self.res_icon_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.res_icon_list.setWordWrap(True)
        self.res_icon_list.setMovement(QListView.Movement.Static)
        self.res_icon_list.setStyleSheet("""
            QListWidget { background-color: #CBE9CF; border: 1px solid #B2D3B6; border-radius: 4px; color: #1E361F; }
            QListWidget::item { border-radius: 6px; padding: 6px; }
            QListWidget::item:hover { background-color: #B8DCBD; }
            QListWidget::item:selected { background-color: #98C79F; color: #0A1A0B; }
        """)
        self.res_icon_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.res_icon_list.customContextMenuRequested.connect(
            self.show_resource_context_menu
        )
        resources_layout.addWidget(self.res_icon_list)
        main_splitter.addWidget(resources_area)

        # 左右各占 50% 比例
        main_splitter.setSizes([500, 500])
        layout.addWidget(main_splitter)

    @Slot(str)
    def filter_assets(self, text: str):
        search_text = text.strip().lower()
        for i in range(self.icon_list.count()):
            item = self.icon_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    @Slot(str)
    def filter_resources(self, text: str):
        search_text = text.strip().lower()
        for i in range(self.res_icon_list.count()):
            item = self.res_icon_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def refresh_asset_folders(self):
        self.combo_assets.blockSignals(True)
        self.combo_assets.clear()
        subdirs = []
        if self.assets_base_dir.exists():
            subdirs = [
                d.name
                for d in self.assets_base_dir.iterdir()
                if d.is_dir() and not d.name.startswith(("_", "."))
            ]
            subdirs.sort()

        if not subdirs:
            self.combo_assets.addItem("未找到资产目录")
            self.combo_assets.setEnabled(False)
        else:
            self.combo_assets.setEnabled(True)
            self.combo_assets.addItems(subdirs)
        self.combo_assets.blockSignals(False)

        if subdirs:
            default_idx = subdirs.index("icons") if "icons" in subdirs else 0
            self.combo_assets.setCurrentIndex(default_idx)
            self.on_asset_folder_changed(self.combo_assets.currentText())

    def refresh_resource_folders(self):
        self.combo_resources.blockSignals(True)
        self.combo_resources.clear()
        subdirs = []
        if self.resources_base_dir.exists():
            subdirs = [
                d.name
                for d in self.resources_base_dir.iterdir()
                if d.is_dir() and not d.name.startswith(("_", "."))
            ]
            subdirs.sort()

        if not subdirs:
            self.combo_resources.addItem("未找到资源目录")
            self.combo_resources.setEnabled(False)
        else:
            self.combo_resources.setEnabled(True)
            self.combo_resources.addItems(subdirs)
        self.combo_resources.blockSignals(False)

        if subdirs:
            target_name = (
                self.current_asset_folder
                if self.current_asset_folder in subdirs
                else subdirs[0]
            )
            self.combo_resources.setCurrentText(target_name)
            self.on_resource_folder_changed(self.combo_resources.currentText())

    @Slot(str)
    def on_asset_folder_changed(self, folder_name: str):
        if not folder_name or folder_name == "未找到资产目录":
            return
        self.current_asset_folder = folder_name
        self.search_input_assets.clear()
        self.refresh_asset_icons()

    @Slot(str)
    def on_resource_folder_changed(self, folder_name: str):
        if not folder_name or folder_name == "未找到资源目录":
            return
        self.current_resource_folder = folder_name
        self.search_input_resources.clear()
        self.refresh_resource_icons()

    def refresh_asset_icons(self):
        self.icon_list.clear()
        if not self.current_asset_folder:
            return

        target_dir = self.assets_base_dir / self.current_asset_folder
        if not target_dir.exists():
            return

        pattern = re.compile(r"^\d+-(.+)\.(svg|png|jpg|jpeg|ico)$", re.IGNORECASE)
        image_files = [
            p
            for p in target_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".ico"}
        ]
        image_files.sort(key=lambda x: x.name)

        for img_path in image_files:
            icon = QIcon(str(img_path))
            display_name = img_path.name
            match = pattern.match(display_name)
            if match:
                display_name = match.group(1) + img_path.suffix.lower()
            item = QListWidgetItem(icon, display_name)
            item.setToolTip(f"物理文件名: {img_path.name}\n双击复制到下方资源库")
            item.setData(Qt.ItemDataRole.UserRole, str(img_path))
            self.icon_list.addItem(item)

    def refresh_resource_icons(self):
        self.res_icon_list.clear()
        if not self.current_resource_folder:
            return

        target_dir = self.resources_base_dir / self.current_resource_folder
        if not target_dir.exists():
            return

        pattern = re.compile(r"^\d+-(.+)\.(svg|png|jpg|jpeg|ico)$", re.IGNORECASE)
        image_files = [
            p
            for p in target_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".ico"}
        ]
        image_files.sort(key=lambda x: x.name)

        for img_path in image_files:
            icon = QIcon(str(img_path))
            display_name = img_path.name
            match = pattern.match(display_name)
            if match:
                display_name = match.group(1) + img_path.suffix.lower()
            item = QListWidgetItem(icon, display_name)
            item.setToolTip(f"已在资源库中: {img_path.name}\n右键可删除")
            item.setData(Qt.ItemDataRole.UserRole, str(img_path))
            self.res_icon_list.addItem(item)

        if (
            hasattr(self, "search_input_resources")
            and self.search_input_resources.text()
        ):
            self.filter_resources(self.search_input_resources.text())

    @Slot(QListWidgetItem)
    def publish_single_icon(self, item):
        file_path = Path(item.data(Qt.ItemDataRole.UserRole))
        if not self.current_asset_folder:
            return

        target_resource_dir = self.resources_base_dir / self.current_asset_folder
        target_resource_dir.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            return
        dest_path = target_resource_dir / file_path.name
        try:
            shutil.copy2(file_path, dest_path)
            print(f"🚀 已将 {file_path.name} 复制至资源库: {dest_path}")
            self.refresh_resource_folders()
            self.combo_resources.setCurrentText(self.current_asset_folder)
        except Exception as e:
            QMessageBox.warning(self, "复制失败", f"无法复制文件:\n{e}")

    @Slot(object)
    def show_resource_context_menu(self, pos):
        item = self.res_icon_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #ffffff; border: 1px solid #cccccc; padding: 4px; }
            QMenu::item { padding: 6px 24px; color: #333333; font-weight: bold; }
            QMenu::item:selected { background-color: #cce4f7; color: #000000; }
        """)

        delete_action = QAction("❌ 删除该资源", self)
        delete_action.triggered.connect(lambda: self.delete_resource_file(item))
        menu.addAction(delete_action)

        menu.exec(self.res_icon_list.mapToGlobal(pos))

    def delete_resource_file(self, item):
        file_path = Path(item.data(Qt.ItemDataRole.UserRole))
        file_name = item.text()

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(
            f"确定要从资源库中永久删除 {file_name} 吗?\n(该操作不会影响上方 assets 里的原文件)"
        )
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            try:
                if file_path.exists():
                    file_path.unlink()
                    print(f"🗑️ 已从资源库删除: {file_path.name}")
                    self.refresh_resource_icons()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"无法删除文件(可能被占用):\n{e}")

    def start_manual_build(self):
        if not self.current_resource_folder:
            QMessageBox.warning(self, "提示", "请先在下方选择一个资源目录!")
            return

        target_dir = self.resources_base_dir / self.current_resource_folder
        if not target_dir.exists():
            QMessageBox.warning(self, "提示", f"该资源目录不存在:\n{target_dir}")
            return

        self.btn_build.setEnabled(False)
        print(f"\n⚙️ 正在更新 .qrc: [{self.current_resource_folder}] ...")

        self.builder_worker = ResourceBuilderWorker(target_dir=str(target_dir))
        self.builder_worker.log_signal.connect(print)
        self.builder_worker.finished_signal.connect(self.build_finished)
        self.builder_worker.start()

    @Slot(bool, str)
    def build_finished(self, success, msg):
        self.btn_build.setEnabled(True)
        if success:
            print(f"\n🎉 {msg}")
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "构建失败", msg)
