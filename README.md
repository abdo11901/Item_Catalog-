Project name:  
====================
Item-Catalog: The Item Catalog project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system.

Prerequisite:  
====================
* Python 3
* vagrant https://www.vagrantup.com/downloads.html
* virtualbox  https://www.virtualbox.org/wiki/Download_Old_Builds_5_1

Files List:  
====================
* database_setup.py
* demo.py
* README.md

Files explanation  
====================
* database_setup.py: contains the database
* demo.py: contains the routes 
* README.md: contains a description of our project

  How to run it:  
  ====================
 1-Run the vagrant: 
  * -vagrant up
  * -vagrant ssh
  * -cd /vagrant/
  * -cd Item-Catalog
  * -python demo.py
    
 2-open your browser and write:
  * -localhost:5000/
