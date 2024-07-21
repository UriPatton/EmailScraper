import asyncio
import re
from typing import List, Dict
from urllib.parse import urlparse, urljoin, urlunparse

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pydantic import AnyHttpUrl
from rq import get_current_job


class AsyncEmailScraper:
    def __init__(self,
                 base_url,
                 max_pages=100,
                 max_workers=50,
                 all_pages: int = 0,
                 current_page: int = 1
                 ):
        self.job = get_current_job()
        self.all_pages = all_pages
        self.current_page = current_page
        self.base_url = base_url
        self.visited_urls = set()
        self.invalid_urls = set()
        self.max_pages = max_pages
        self.emails = set()
        self.to_visit_urls = asyncio.Queue()
        self.max_workers = max_workers
        self.user_agent = UserAgent()
        self.semaphore = asyncio.Semaphore(max_workers)
        # Compile the email regex pattern once for efficiency
        self.email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    async def fetch(self, url):
        async with self.semaphore:
            try:
                headers = {'User-Agent': self.user_agent.random}
                async with self.session.get(url, headers=headers) as response:
                    # check content type
                    if not self.valid_content_type(response.headers.get('content-type', '')):
                        self.invalid_urls.add(url)
                        return ""
                    # Consider using response.raise_for_status() to catch HTTP error responses
                    if response.status not in range(400, 499):
                        result = await response.text()
                        self.visited_urls.add(url)
                        return result
                    response.raise_for_status()
            except Exception as e:
                self.visited_urls.add(url)
                return ""

    async def extract_emails(self, content):
        # Use the compiled regex pattern
        emails_set = set(self.email_pattern.findall(content))
        self.emails.update(emails_set)

    def valid_content_type(self, content_type):
        return any(ct in content_type for ct in ['text/html', 'application/xhtml+xml'])

    def invalid_extension(self, url):
        invalid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.mp3', '.avi', '.mov', '.webm',
                              '.zip', '.rar', '.tar', '.gz', '.7z', '.exe', '.dmg', '.iso', '.apk', '.deb', '.rpm', ]
        return any(url.endswith(ext) for ext in invalid_extensions)

    def clean_url(self, url):
        # Clean the URL by removing query parameters and fragments
        parsed_url = urlparse(url)
        return urlunparse(parsed_url._replace(query='', fragment=''))

    async def extract_links(self, _url, content):
        domain = urlparse(_url).netloc
        soup = BeautifulSoup(content, 'html.parser')
        for anchor in soup.find_all('a', href=True):
            link = anchor['href']
            if not urlparse(link).netloc:
                link = urljoin(_url, link)
            cleaned_url = self.clean_url(link)
            if cleaned_url in self.invalid_urls:
                continue
            if self.invalid_extension(cleaned_url):
                self.invalid_urls.add(cleaned_url)
                continue
            if (domain == urlparse(cleaned_url).netloc and cleaned_url not in self.visited_urls and
                    (self.to_visit_urls.qsize() + len(self.visited_urls)) < self.max_pages):
                # Check if URL is already in the queue to avoid duplicate work
                if cleaned_url not in self.to_visit_urls._queue and cleaned_url not in self.visited_urls:
                    await self.to_visit_urls.put(cleaned_url)

    async def worker(self):
        while True:
            url = await self.to_visit_urls.get()
            try:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    content = await self.fetch(url)
                    if content:
                        await self.extract_links(url, content)
                        await self.extract_emails(content)
            finally:
                self.to_visit_urls.task_done()
                if self.to_visit_urls.empty() or len(self.visited_urls) >= self.max_pages:
                    break

    async def run(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as self.session:
            await self.to_visit_urls.put(self.base_url)
            workers = [asyncio.create_task(self.worker()) for _ in range(self.max_workers)]
            await self.to_visit_urls.join()
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)


def scrap_emails(domains: list[AnyHttpUrl], max_worker: int, max_pages: int) -> List[Dict[str, List]]:
    emails = {}
    for index, domain in enumerate(domains, start=1):
        domain_str = str(domain)
        email_scraper = AsyncEmailScraper(
            domain_str,
            max_pages=max_pages,
            max_workers=max_worker,
            all_pages=len(domains),
            current_page=index
        )
        try:
            asyncio.run(email_scraper.run())
            job = get_current_job()
            job.meta['percentage'] = int((index / len(domains)) * 100)
            job.save_meta()
        except Exception as e:
            print(f"Failed to run email scraper: {e}, for domain: {domain}")
        emails[domain_str] = list(email_scraper.emails)
    return [emails]


if __name__ == '__main__':
    domains = ["https://zeptos.ge", "https://www.google.com", "https://www.facebook.com"]
    result = scrap_emails(domains, 100, 100)
    print(f"Found emails: {result}")
