# import typer
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# from core.mongo_connect import MongoConnect
# from utilities.vectorstore import PineconeVectorStoreHandler
# from .base_command import BaseCommand
# from rich.console import Console
# from rich.progress import track
# import logging
# from datetime import datetime
# import time
# import asyncio
# import nest_asyncio
# from crawl4ai import AsyncWebCrawler, CacheMode, BrowserConfig, CrawlerRunConfig

# nest_asyncio.apply()

# console = Console()

# class ScraperCommand(BaseCommand):
#     def __init__(self):
#         self.base_url = "https://support.studiesweekly.com/hc/en-us"
#         self.visited = set()
        
        

#     def is_internal(self, url):
#         parsed = urlparse(url)
#         return parsed.netloc == urlparse(self.base_url).netloc

#     def get_links(self, soup, current_url):
#         links = set()
#         for a in soup.find_all("a", href=True):
#             href = urljoin(current_url, a['href'])
#             if self.is_internal(href) and href.startswith(self.base_url):
#                 links.add(href.split("#")[0])
#         return links

#     def extract_text(self, soup):
#         # Remove scripts/styles
#         for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
#             tag.decompose()
#         # Get visible text
#         text = soup.get_text(separator="\n", strip=True)
#         return text

#     async def fetch_page(self, url, crawler):
#         try:
#             result = await crawler.arun(url=url)
#             return result
#         except Exception as e:
#             logging.error(f"Failed to load {url} with AsyncWebCrawler: {str(e)}")
#             return None

#     async def scrape_site(self):
#         to_visit = {self.base_url}
#         all_data = []
#         self.mongo_collection = MongoConnect.get_collection('support_index')
#         crawler_run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
#         async with AsyncWebCrawler() as crawler:
#             while to_visit:
#                 url = to_visit.pop()
#                 console.print(f"Scraping: {url}")
#                 if url in self.visited:
#                     continue
#                 try:
#                     page_source = await self.fetch_page(url, crawler)
#                     if not page_source:
#                         continue
#                     soup = BeautifulSoup(page_source.markdown.raw_markdown, "html.parser")
#                     title = soup.title.string.strip() if soup.title else ""
#                     text = self.extract_text(soup)
#                     if text and len(text) > 100:
#                         meta = {
#                             "title": title,
#                             "type": "support",
#                             "url": url,
#                             "scraped_at": str(datetime.now())
#                         }
#                         all_data.append({"text": text, "metadata": meta})
#                         self.mongo_collection.update_one(
#                             {"url": url},
#                             {"$set": meta},
#                             upsert=True
#                         )
#                     links = self.get_links(soup, url)
#                     to_visit.update(links - self.visited)
#                     self.visited.add(url)
#                     await asyncio.sleep(1)
#                 except Exception as e:
#                     logging.error(f"Failed to scrape {url}: {str(e)}")
#         return all_data

#     def chunk_text(self, text, metadata):
#         # Simple chunking by paragraphs, max 800 chars
#         chunks = []
#         current = ""
#         for para in text.split("\n\n"):
#             if len(current) + len(para) < 800:
#                 current += para + "\n\n"
#             else:
#                 if current:
#                     chunks.append({"text": current.strip(), "metadata": metadata})
#                 current = para + "\n\n"
#         if current:
#             chunks.append({"text": current.strip(), "metadata": metadata})
#         return chunks

#     def register(self, app: typer.Typer) -> None:
#         @app.command()
#         def scraper(
#             verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
#         ):
#             """Scrape support.studiesweekly.com and add content to Pinecone"""
#             try:
#                 if verbose:
#                     console.print("[bold blue]Starting support site scraping...[/bold blue]")
                    
#                     console.print("[bold red]Scraping is disabled due to Server Security...[/bold red]")
#                 self.vector_store = PineconeVectorStoreHandler()
#                 # all_data = asyncio.run(self.scrape_site())
#                 # chunked = []
#                 # for item in track(all_data, description="Chunking..."):
#                 #     chunked.extend(self.chunk_text(item["text"], item["metadata"]))
#                 # if verbose:
#                 #     console.print(f"[bold blue]Scraped {len(all_data)} pages and chunked into {len(chunked)} chunks.[/bold blue]")
#                 #     console.print(f"Uploading {len(chunked)} chunks to Pinecone...")
#                 # self.vector_store.add_texts(
#                 #     [c["text"] for c in chunked],
#                 #     metadatas=[c["metadata"] for c in chunked]
#                 # )
#                 # if verbose:
#                 #     console.print("[bold green]Support site scraping and upload complete![/bold green]")
#             except Exception as e:
#                 console.print(f"[bold red]Error during scraping: {str(e)}[/bold red]")
#                 raise typer.Exit(code=1)
