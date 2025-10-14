import os
from pathlib import Path


def show_tree(path='.', prefix='', max_depth=5, current_depth=0, ignore=None):
    if ignore is None:
        ignore = {
            '.venv', 'venv', '.vscode', '__pycache__', 
            'build', '.git', 'node_modules',
            '.pytest_cache', '.mypy_cache', '.tox',
            'htmlcov', '.coverage', '.eggs', '*.egg-info'
        }
    
    if current_depth >= max_depth:
        return
    
    path = Path(path)
    
    try:
        items = sorted(
            [p for p in path.iterdir() 
             if p.name not in ignore and not p.name.startswith('.')],
            key=lambda x: (x.is_file(), x.name)
        )
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            icon = '📄' if item.is_file() else '📁'
            print(f"{prefix}{'└── ' if is_last else '├── '}{icon} {item.name}")
            
            if item.is_dir():
                show_tree(
                    item, 
                    prefix + ('    ' if is_last else '│   '), 
                    max_depth, 
                    current_depth + 1, 
                    ignore
                )
    except PermissionError:
        pass


if __name__ == '__main__':
    print("\n📁 PROJECT STRUCTURE:\n")
    print(f"📁 {Path.cwd().name}/")
    show_tree()
