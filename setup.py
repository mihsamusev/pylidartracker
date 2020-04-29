from setuptools import setup, find_packages 
  
setup( 
        name ='pylidartracker', 
        version ='1.0.1', 
        author ='Mihhail Samusev', 
        author_email ='msam@build.aau.dk', 
        url ='https://github.com/mihsamusev/pylidartracker', 
        description ='UI for processing of data collected with Velodyne lidar', 
        long_description = "Check the GitHub homepage for getting started", # TODO: add DESCRIPTION.txt that is excluded
        license ='MIT',
        package_dir={"": "src"},
        py_modules=["app","controller","imageresource"],
        packages=["ui","processing"],
        #include_package_data=True,
        #package_data={'src/images': ['images/*.png']},
        install_requires = [
            "dpkt",
            "numpy",
            "scikit-image",
            "scikit-learn",
            "scipy",
            "PyQt5==5.13",
            "pyopengl",
            "pyqtgraph",
        ], 
        entry_points ={ 
            'console_scripts': [ 
                'pylidartracker = app:main'
            ] 
        },
        classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3',
          "Operating System :: OS Independent"
          ],
        keywords="lidar tracking clustering traffic analysis processing velodyne"
) 
