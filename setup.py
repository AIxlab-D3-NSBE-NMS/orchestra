from setuptools import setup, find_packages

setup(
    name='orchestra',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here, e.g.:
        'fastapi', 'uvicorn'
        # 'ffmpeg-python'
    ],
    author='Diogo Duarte',
    description='orchestration system for distributed media streaming. Developed at the AI X Lab, D^3 Digital Data Design Institute by NOVA SBE and NOVA Medical School'',
    url='https://github.com/AIxlab-D3-NSBE-NMS/orchestra',
)

