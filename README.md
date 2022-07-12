# myBookshelf
Simple web application for collections of books. Still in development.
* Created by: www.linkedin.com/in/arturwrzosek
* Application is hosted at: http://arturwrzosek.pythonanywhere.com/
* Tech stack:
  * Python 3.9
  * Django 4.0.1
  * djangoRESTframework 3.13.1 
  * SQLite
  * requests 2.27
  * Bootstrap 5.0
* application is covered with unit tests
* application got also simple REST API build in DRF

## Functionality
*Anonymous user* can:
* search for a books, authors, categories and publishers added to *myBookshelf* database
* search for a book in *Google Books* database with title, authors, publisher or ISBN number

*Signed and logged-in user* can also:
* add a new book, author, category or publisher to *myBookshelf* database
* editing any of above, but can only delete objects which were created by himself
* add a new book with data from *Google Books* to *myBookshelf* database
* rate any book with vote from 1 to 10
* add any book to *owned* collection
* search for other users profiles
* add any user to *friends* list
* look at books and other friends in any *friendly* profile
