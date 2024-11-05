# Shopping
Edited app.py Oct 12th/
- re-wrote @app.route('/cart') function
- added @app.route('/remove_item) function
  
Edited cart.html Oct 12th/
- edit quantity control/forms
- edit quantity buttons
- added remove button
- added summary container
- added summary container label
- edit total price
- re-wrote pricing body
- edit quantity functions
- implemented item removal/trash can
- implemented summary section
- implemented checkout button & function
  
New cart and checkout changes (Oct 30th)
- will need to add top nav bar on the cart page

app.py minor changes which fixes all the numbers and calculations issues on cart and checkout (Oct 30th)
- not up to date with any other changes/additions made by others

static/img update (Oct 30th)
- uploaded a new delete icon

python file update for save for later function (Nov 5th)
- edited code issue linked with moving items from save for later section back into cart

cart html update (Nov 5th)
- cart buttons changes, save for later section
- background edit
- footer implementation

checkout html update (Nov 5th)
- background implementation 
- summery float total change
- payment section changed and added email section

static update (Nov 5th)
- uploaded background img 2.0
- uploaded checkout img delivery

* code for background to be implemented on every HTML *
  body {
            font-family: Arial, sans-serif;
            background-image: url('/static/img/delivery.webp'); /* Replace img location according to the image you want implemented for each page */
            background-size: cover; 
            background-repeat: no-repeat;
            background-position: center;
            background-attachment: fixed; 
            color: #333;
        }
  
  

