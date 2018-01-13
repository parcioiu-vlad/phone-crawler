from src.gsmarena.crawler import Crawler
from src.imeiinfo.ImeiInfoCrawler import ImeiInfoCrawler


def main():
    # crawler = Crawler()
    crawler = ImeiInfoCrawler()
    crawler.crawl()

if __name__ == "__main__":
    import logging.config

    logging.config.fileConfig('logging.ini')
    main()
