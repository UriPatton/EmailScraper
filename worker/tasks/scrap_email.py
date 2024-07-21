import asyncio
import re
from urllib.parse import urlparse, urljoin, urlunparse
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class AsyncEmailScraper:
    def __init__(self, base_url, max_pages=100, max_workers=50):
        self.base_url = base_url
        self.visited_urls = set()
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


def scrap_emails(domains: list, max_worker: int, max_pages: int) -> list:
    emails = []
    for domain in domains:
        email_scraper = AsyncEmailScraper(str(domain), max_pages=max_pages, max_workers=max_worker)
        try:
            asyncio.run(email_scraper.run())
        except Exception as e:
            print(f"Failed to run email scraper: {e}, for domain: {domain}")
        emails.extend(email_scraper.emails)
    return emails
