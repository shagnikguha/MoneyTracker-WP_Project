# Money Tracker

A comprehensive web application for tracking personal finances, built with Django and Bootstrap. Money Tracker helps users manage their daily transactions, view spending history, and analyze their financial patterns through visual analytics.

## Features

- **User Authentication**
  - Secure login and registration system
  - Password protection for personal financial data

- **Transaction Management**
  - Add income and expense transactions
  - Categorize transactions (Food, Travel, Shopping, etc.)
  - Mark transactions as recurring
  - Edit and delete transactions
  - Add transaction descriptions

- **Financial Overview**
  - Today's transactions summary
  - Complete transaction history
  - Visual analytics with charts and graphs
  - Category-wise expense breakdown

- **User Interface**
  - Clean, modern design with mauve theme
  - Responsive layout for all devices
  - Intuitive navigation
  - Interactive data visualization

## Technology Stack

- **Backend**: Django 5.2
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (default Django database)
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Charts**: Chart.js

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/MoneyTracker.git
cd MoneyTracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Access the application at `http://127.0.0.1:8000`

## Project Structure

```
MoneyTracker/
├── main/
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── today_transactions.html
│   │   ├── transaction_history.html
│   │   └── edit_transaction.html
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── MoneyTracker/
│   ├── settings.py
│   └── urls.py
└── manage.py
```

## Usage

1. Register a new account or login with existing credentials
2. Add new transactions from the "Today's Transactions" page
3. View all transactions in the "Transaction History" page
4. Edit or delete transactions as needed
5. Monitor spending patterns through visual analytics

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django documentation and community
- Bootstrap team for the excellent UI framework
- Chart.js team for visualization capabilities
- Font Awesome for the comprehensive icon set
