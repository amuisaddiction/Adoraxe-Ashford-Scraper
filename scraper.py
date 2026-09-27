"""
Adoraxe - Ashford, CT SearchIQS Land Records Scraper

Discovery-first scaffold.
The live SearchIQS HTML structure should be inspected before implementing
site-specific selectors/postbacks.
"""

from datetime import date, timedelta


def get_date_window(days_back: int = 80):
    """Return the dynamic inclusive date window ending today."""
    today = date.today()
    from_date = today - timedelta(days=days_back)
    return from_date, today


def main():
    from_date, to_date = get_date_window(80)
    print("Ashford, CT SearchIQS scraper")
    print(f"From date: {from_date}")
    print(f"To date:   {to_date}")
    print("Discovery mode and live-site navigation will be implemented next.")


if __name__ == "__main__":
    main()
