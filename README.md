# Item Catalog

## This project employs both the front end technologies such as html, css, JavaScript, and bootstrap, as well as back end technologies, such as Python, SQL, Flask. A user will see the homepage of items created by different users or view items of a specific category. A user can also securely log in with his or her Google account and then add a new item, and edit or delete his or her own item.

## Requirement for Running:
### This project is built on python and frameworks like SQL Alchemy, and Flask, you can download [Vagrant](https://www.vagrantup.com/) to run this project. Vagrant is a powerful virtual machine tool and contains all the necessary frameworks. You also need to have a Google account and create your own client ID and client Secrets from [Google API](https://console.cloud.google.com/home) for log in purposes.

## After fulfilling the pre-requirements, you can follow the steps below to set up a database and run the program:
1. Download and unzip the project folder and put it to the same directory of your Vagranfile.
2. Replace the client ID and client secretes in your login.html and client_secrets.json to your own.
3. After booting your vagrant machine up and setting a ssh key, change directory to /vagrant/catalog
4. Run the command python database_setup.py to set up the databse.
5. Optional: Run python lotsofitems.py to randomly create 20 items with random names, categories, descriptions, and user_id of 1 to 20. **WARNING:  Doing so will delete all items in the current database.** The purpose of this file is to make quick test of main.py and its templates without manually creating a lot of items.
6. Run python main.py. Then open your web browser and visit http://localhost:5000/ and you will see the homepage of this project.

## You can now view all the items, and log in to add, edit, and delete your own items.