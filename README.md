## orchestra

repository for experiment code and experiment control at the AI X Lab

Folder structure:
- ansible: ansible playbooks for deploying experiment code and controlling hosts
- demos: demo code for emotion recognition with deepface
- experiments: experiment code, subfolders for different experiments
- deprecated: deprecated code
- tests: hardware tests mainly owl cameras





| File  | Use  |
|-------|------|
| `README.md`               | The file you're reading  |
| `LICENSE`                 | [Simplified BSD License](https://opensource.org/license/bsd-2-clause) |
| `setup.py`                | setup file to install repo (can be run without installing ofc) |
| `__init__.py`             | required placeholder to install this repo (à la pip install)   |
| `Makefile`                | instructions for `make` or `make install` if repo is installed in linux |
| `requirements.txt`        | specifies the dependencies to create similar env |
| `requirements_docker.txt` | same as above but for `docker` |
| `pyproject.toml`          | uv spec file (to create virtual environments) |
| `uv.lock`                 | file that specifies the environment according to [uv](https://docs.astral.sh/uv/concepts/projects/sync/) |
