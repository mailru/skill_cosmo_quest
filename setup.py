#!/usr/bin/env python

import os

from setuptools import find_packages, setup

VERSION = os.getenv("CI_COMMIT_TAG")
if not VERSION:
    VERSION = "0.0.1"

# --- >
setup(
    name="skill-space-quest",
    version=VERSION,
    package_dir={"skill_cosmo_quest": "src/skill_cosmo_quest"},
    python_requires=">=3.6",
    packages=find_packages(where="src", include=["skill_cosmo_quest"]),
    url="https://gitlab.com/mailru-voice/external_skills/skill_cosmo_quest",
    license="MIT",
    author="n.andreev",
    author_email="nickandreevart@gmail.com",
    description="skill-cosmo-quest",
)
