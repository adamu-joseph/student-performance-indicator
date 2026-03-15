from setuptools import find_packages, setup
from typing import List

def get_requirements(file_path:str)->List[str]:
    """
    this functionn will return the list of requirements"""
    with open(file_path) as file_obj:
        requirements = [req.strip() for req in file_obj if req!="-e ."]




setup(
    name="mlproject", 
    version="0.0.1",
    author="Adamu Joseph", 
    author_email="ohigwerejosephadamu@gmail.com",
    packages=find_packages(), 
    install_requires=get_requirements("requirements.txt")

)