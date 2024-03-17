import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

def get_job_description(job_url, scraper):
    job_response = scraper.get(job_url)
    job_soup = BeautifulSoup(job_response.text, "html.parser")
    job_description_div = job_soup.find('div', class_='jobsearch-jobDescriptionText')
    job_description = job_description_div.get_text(strip=True) if job_description_div else 'No Description Found'
    return job_description

def scrape_jobs(job_title, location):
    # Encode the job title and location to be URL-friendly
    encoded_job_title = '+'.join(job_title.split())
    encoded_location = '+'.join(location.split())
    base_url = f"https://ca.indeed.com/jobs?q={encoded_job_title}&l={encoded_location}"
    scraper = cloudscraper.create_scraper()
    response = scraper.get(base_url)

    bs = BeautifulSoup(response.text, "html.parser")
    job_cards = bs.find_all('div', class_='slider_item')

    info = []
    
    for card in job_cards:
        job_seen_beacon = card.find('div', class_='job_seen_beacon')
        if job_seen_beacon:
            # Extract the job title and link.
            TITLE = job_seen_beacon.find('h2', class_='jobTitle')
            title = TITLE.get_text(strip=True) if TITLE else 'No Title Found'
            link_tag = TITLE.find('a') if TITLE else None
            link = link_tag['href'] if link_tag else None

            # Construct the full URL.
            if link:
                full_url = f'https://ca.indeed.com{link}'
                job_description = get_job_description(full_url, scraper)
            else:
                full_url = 'No URL Found'
                job_description = 'No Description Found'
            
            # Extract the company name and location using the data-testid attribute.
            company_span = job_seen_beacon.find('span', {'data-testid': 'company-name'})
            company_name = company_span.get_text(strip=True) if company_span else 'No Company Name Found'
            location_div = job_seen_beacon.find('div', {'data-testid': 'text-location'})
            company_location = location_div.get_text(strip=True) if location_div else 'No Location Found'
            
            data = {
                'title': title,
                'company name': company_name,
                'company location': company_location,
                'url': full_url,
                'description': job_description
            }
            info.append(data)
    
    # Create a DataFrame from the list of dictionaries
    job_df = pd.DataFrame(info)
    return job_df

if __name__ == "__main__":
    job_title = "data intern"
    location = "Mississauga, ON"
    df = scrape_jobs(job_title, location)
    print(df)
    # Optionally save the DataFrame to a CSV file
    df.to_csv('job_listings.csv', index=False)
