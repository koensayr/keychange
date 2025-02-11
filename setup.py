from setuptools import setup, find_packages

setup(
    name="keychange",
    version="0.2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "librosa>=0.10.1",
        "numpy>=1.24.0",
        "sounddevice>=0.4.6",
        "soundfile>=0.12.1",
        "python-vst3>=1.3.0",
        "pysrt>=1.2.0",  # SRT protocol support
        "av>=10.0.0",    # Audio/video container support
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-mock>=3.11.1",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "isort>=5.12.0",
        ],
        "examples": [
            "rich>=13.5.2",
        ]
    },
    python_requires=">=3.8",
    description="A Python application for detecting musical keys in audio files and streams",
    author="KeyChange Team",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
    ],
    entry_points={
        'console_scripts': [
            'keychange=keychange.cli:main',
        ],
    },
)
