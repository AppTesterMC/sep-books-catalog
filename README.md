# SEP Books Catalog

[Visit the Catalog](https://apptestermc.github.io/sep-books-catalog/)

A beautiful, automatically-updated catalog of books from Σύγχρονη Εποχή Εκδόσεις (sep.gr), hosted on GitHub Pages.

## 🌟 Features

- **Automated Daily Updates**: GitHub Actions scrapes book data every day at 3 AM UTC
- **Beautiful Interface**: Modern, literary-inspired design with smooth animations
- **Real-time Search**: Filter books by title, author, publisher, or ISBN
- **Category Filtering**: Browse by book category
- **Flexible Sorting**: Sort by title, author, price, date, or pages
- **Responsive Design**: Works beautifully on desktop and mobile devices
- **Performance**: Fast loading with efficient data handling

## 🚀 Quick Start

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/AppTesterMC/sep-books-catalog.git
cd sep-books-catalog
```

### 2. Enable GitHub Pages

1. Go to your repository settings
2. Navigate to **Pages** section (in the left sidebar)
3. Under **Source**, select:
   - Branch: `main`
   - Folder: `/` (root)
4. Click **Save**
5. Your site will be available at `https://YOUR-USERNAME.github.io/sep-books-catalog/`

### 3. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. The scraper will now run automatically every day

### 4. Initial Data Setup (Optional)

To populate data immediately without waiting for the scheduled run:

1. Go to **Actions** tab
2. Click on **"Scrape Books Data"** workflow
3. Click **"Run workflow"** dropdown
4. Click the green **"Run workflow"** button

The scraper will run and commit the data automatically.

## 📁 Project Structure

```
sep-books-catalog/
├── .github/
│   └── workflows/
│       └── scrape.yml          # GitHub Actions workflow
├── data/
│   └── latest.csv              # Latest scraped book data (auto-generated)
├── index.html                  # Main webpage
├── style.css                   # Styles
├── script.js                   # JavaScript for interactivity
├── scraper.py                  # Python web scraper
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- pip

### Running the Scraper Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the scraper:
```bash
python scraper.py
```

The data will be saved in the `data/` directory.

### Testing the Website Locally

Simply open `index.html` in your browser, or use a local server:

```bash
# Python
python -m http.server 8000

# Node.js (if you have http-server installed)
npx http-server
```

Then visit `http://localhost:8000`

## ⚙️ Configuration

### Changing Scrape Schedule

Edit `.github/workflows/scrape.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '0 3 * * *'  # Runs at 3 AM UTC daily
```

[Cron syntax reference](https://crontab.guru/)

### Customizing Categories

Edit the `thislist` array in `scraper.py` to add or remove categories:

```python
thislist = [
    "biblia-poy-diathetei-h-se",
    "vivlia-allon-ekdoton",
    # Add more categories here
]
```

### Styling

All styles are in `style.css`. Key CSS variables are defined at the top for easy theming:

```css
:root {
    --primary-bg: #faf8f5;
    --accent-color: #8b4513;
    /* Modify these to change the color scheme */
}
```

## 🔧 Troubleshooting

### GitHub Actions Not Running

- Ensure Actions are enabled in your repository settings
- Check if your repository is active (Actions pause after 60 days of inactivity)
- Verify the workflow file syntax is correct

### No Data Showing on Website

- Check if `data/latest.csv` exists in your repository
- Run the workflow manually to generate initial data
- Check browser console for errors

### Scraper Errors

- The website structure may have changed - check the CSS selectors in `scraper.py`
- Verify you have all dependencies installed
- Check rate limiting or connection issues

## 📊 Data Structure

The CSV file contains the following columns:

- `title` - Book title
- `author` - Author name
- `publisher` - Publisher name
- `ISBN` - ISBN number
- `category` - Book category
- `date` - Publication date
- `pages` - Number of pages
- `price` - Original price
- `discount_price` - Discounted price (if available)

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📝 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

This project scrapes data from sep.gr for personal and educational purposes. Please respect the website's terms of service and robots.txt file. Consider adding appropriate rate limiting and user-agent headers if you plan to scrape frequently.

## 🙏 Credits

- Data source: [sep.gr](https://sep.gr)
- Fonts: [Crimson Pro](https://fonts.google.com/specimen/Crimson+Pro) & [Work Sans](https://fonts.google.com/specimen/Work+Sans)
- Icons: Custom SVG icons

---

Made with ❤️ for book lovers
