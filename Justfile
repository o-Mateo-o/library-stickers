test:
    pytest

pc:
    pre-commit run --all-files

mypy:
    mypy src/
