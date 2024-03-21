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
            # Find all numbers in the posted_text, assuming that the first number is the number of days
            numbers = [int(s) for s in posted_text.split() if s.isdigit()]
            if numbers:
                # Assuming the format 'X days ago', where X is the first number found
                return datetime.now().date() - timedelta(days=numbers[0])

    return None


def scrape_jobs(job_titles, locations, existing_urls):
    scraper = cloudscraper.create_scraper()
    new_jobs_info = []

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

                    if link:
                        full_url = f'https://ca.indeed.com{link}'
                        if not existing_df['url'].str.contains(full_url).any():
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
                        # 'description': job_description # This line is commented out
                        'posting_date': posting_date,
                        'already_applied': 'No'
                    }
                    new_jobs_info.append(data)

    if new_jobs_info:
        new_jobs_df = pd.DataFrame(new_jobs_info)
        updated_df = pd.concat([existing_df, new_jobs_df], ignore_index=True, sort=False)
        updated_df = updated_df.drop_duplicates(subset=['url'], keep='first')
    else:
        updated_df = existing_df

    return new_jobs_info

if __name__ == "__main__":
    job_titles = [
    "data intern",
    "software intern",
    "programming intern",
    "junior developer",
    "machine learning intern",
    "Data Analyst Intern",
    "Junior Data Scientist",
    "Entry-Level Software Engineer",
    "Web Developer Intern",
    "IT Support Technician",
    "System Administrator Trainee",
    "QA Analyst Trainee",
    "DevOps Intern",
    "Business Intelligence Intern",
    "Cloud Support Associate",
    "Entry-Level UX/UI Designer",
    "Application Support Analyst",
    "Technology Consultant Associate",
    "Junior Product Manager",
    "Front-End Developer Intern",
    "Back-End Developer Intern",
    "Mobile Application Developer Intern",
    "Junior Database Administrator",
    "Artificial Intelligence Intern",
    "Embedded Systems Engineer Trainee",
    "SEO Specialist Trainee",
]
    locations = ["Mississauga, ON", "Toronto, ON"] 

    try:
        existing_df = pd.read_csv('job_listings.csv')
        # Ensure the 'already_applied' column exists
        if 'already_applied' not in existing_df.columns:
            existing_df['already_applied'] = 'No'
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['title', 'company name', 'company location', 'url', 'posting_date', 'already_applied'])

    # Get URLs to check for duplicates
    existing_urls = existing_df['url'].tolist()

    # Scrape the jobs
    new_jobs_info = scrape_jobs(job_titles, locations, existing_urls)

    # Create a DataFrame from the scraped data
    new_jobs_df = pd.DataFrame(new_jobs_info)

    # Append the new jobs to the existing DataFrame if they are not already present
    if not new_jobs_df.empty:
        combined_df = pd.concat([existing_df, new_jobs_df], ignore_index=True, sort=False)
        combined_df.drop_duplicates(subset=['url'], keep='first', inplace=True)
    else:
        combined_df = existing_df

    # Save the combined DataFrame to CSV
    combined_df.to_csv('job_listings.csv', index=False)



