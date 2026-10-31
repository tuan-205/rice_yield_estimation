"""Run all notebook cells using this interpreter, then export web metadata."""
from pathlib import Path
import subprocess
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'notebook/ensemble_training_rice_yield.ipynb'
notebook = nbformat.read(path, as_version=4)
notebook.metadata.kernelspec = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
manager = KernelManager(kernel_name='python3')
manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
client = NotebookClient(notebook, km=manager, timeout=600, allow_errors=False,
                        resources={'metadata': {'path': str(ROOT)}})
try:
    client.execute()
finally:
    if manager.has_kernel:
        manager.shutdown_kernel(now=True)
nbformat.write(notebook, path)
subprocess.run([sys.executable, str(ROOT / 'web/tools/export_browser_model.py')], check=True, cwd=ROOT)
print('Đã chạy toàn bộ notebook, lưu mô hình được chọn và cập nhật dữ liệu web.')
