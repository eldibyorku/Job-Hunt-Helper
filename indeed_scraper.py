import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def get_job_posting_date(card):
    date_span = card.find('span', {'data-testid': 'myJobsStateDate'})
    if date_span:
        posted_text = date_span.text
        
        # Handle the duplication 'PostedPosted X days ago'
        if 'Posted' in posted_text:
            posted_text = posted_text.replace('Posted', '').strip()

        # Check for 'today' or 'yesterday' explicitly
        if 'today' in posted_text.lower():
            return datetime.now().date()
        elif 'yesterday' in posted_text.lower():
            return datetime.now().date() - timedelta(days=1)
        else:
            # Format 'X days ago'          
            numbers = [int(s) for s in posted_text.split() if s.isdigit()]
            if numbers:

                return datetime.now().date() - timedelta(days=numbers[0])

    return None


def scrape_jobs(job_titles, locations, existing_urls):
    scraper = cloudscraper.create_scraper()
    new_jobs_info = []
    exclude_keywords = ["senior", "lead", "manager", "director", "Sr"]

    for job_title in job_titles:
        for location in locations:
            encoded_job_title = '+'.join(job_title.split())
            encoded_location = '+'.join(location.split())
            base_url = f"https://ca.indeed.com/jobs?q={encoded_job_title}&l={encoded_location}&fromage=7"

            response = scraper.get(base_url)
            bs = BeautifulSoup(response.text, "html.parser")
            job_cards = bs.find_all('div', class_='slider_item')

            for card in job_cards:
                job_seen_beacon = card.find('div', class_='job_seen_beacon')
                if job_seen_beacon:
                    TITLE = job_seen_beacon.find('h2', class_='jobTitle')
                    title = TITLE.get_text(strip=True) if TITLE else 'No Title Found'
                    link_tag = TITLE.find('a') if TITLE else None
                    link = link_tag['href'] if link_tag else None

                    if any(exclude_keyword.lower() in title.lower() for exclude_keyword in exclude_keywords):
                        continue  # Skip adding this job if it contains excluded keywords

                    if link:
                        full_url = f'https://ca.indeed.com{link}'
                        if full_url not in existing_urls:
                            # job_description = get_job_description(full_url, scraper) # This line is commented out
                            pass
                        else:
                            continue
                    else:
                        full_url = 'No URL Found'
                        # job_description = 'No Description Found' # This line is commented out

                    company_span = job_seen_beacon.find('span', {'data-testid': 'company-name'})
                    company_name = company_span.get_text(strip=True) if company_span else 'No Company Name Found'
                    location_div = job_seen_beacon.find('div', {'data-testid': 'text-location'})
                    company_location = location_div.get_text(strip=True) if location_div else 'No Location Found'

                    posting_date = get_job_posting_date(job_seen_beacon)

                    data = {
                        'title': title,
                        'company name': company_name,
                        'company location': company_location,
                        'url': full_url,
                        # 'description': job_description # Commented out, not being used atm
                        'posting_date': posting_date,
                        'already_applied': 'No'
                    }
                    new_jobs_info.append(data)
    return new_jobs_info


if __name__ == "__main__":
    job_titles = [
    "junior web developer", "web developer intern",
    "junior front end developer", "front end developer intern",
    "junior back end developer", "back end developer intern",
    "junior software developer", "software developer intern",
    "entry-level machine learning engineer", "machine learning intern",
    "junior data scientist", "data scientist intern",
    "entry-level data analyst", "data analyst intern",
    "junior data engineer", "data engineer intern",
    "entry-level database administrator", "database administrator intern"
    ] 

    locations = ["Mississauga, ON", "Toronto, ON"] 

    try:
        existing_df = pd.read_csv('job_listings.csv')
        if 'already_applied' not in existing_df.columns:
            existing_df['already_applied'] = 'No'
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['title', 'company name', 'company location', 'url', 'posting_date', 'already_applied'])

    # Get existing URLs to check for duplicates.
    existing_urls = existing_df['url'].tolist()
    new_jobs_info = scrape_jobs(job_titles, locations, existing_urls)
    new_jobs_df = pd.DataFrame(new_jobs_info)

    # Append the new jobs to the existing DataFrame if they are not already present
    if not new_jobs_df.empty:
        combined_df = pd.concat([existing_df, new_jobs_df], ignore_index=True, sort=False)
        combined_df.drop_duplicates(subset=['url'], keep='first', inplace=True)
    else:
        combined_df = existing_df

    # Convert 'posting_date' to datetime format for accurate sorting
    combined_df['posting_date'] = pd.to_datetime(combined_df['posting_date'])
    combined_df = combined_df.sort_values(by='posting_date', ascending=False)
    combined_df.to_csv('job_listings.csv', index=False)



