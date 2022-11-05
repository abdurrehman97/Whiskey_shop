import scrapy
import re


class AlcoholSpider(scrapy.Spider):
    name = "alcohol"
    start_urls = ["https://whiskeyshop.com.ua/en/"]
    custom_settings = {'DUPEFILTER_DEBUG': True }

    def parse(self, response, **kwargs):

        alcohol_urls = response.css("li.category a ::attr(href)").getall()
        yield from response.follow_all(alcohol_urls, callback=self.parse_alcohols_shelf)

    def parse_alcohols_shelf(self, response):

        alcohol_list = response.css("#js-product-list .thumbnail-wrapper a::attr(href)").getall()
        yield from response.follow_all(
            alcohol_list,
            callback=self.parse_alcohols_items,
            meta={"listing_url": response.url},
        )

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_alcohols_shelf)

    def parse_alcohols_items(self, response):

        page = response.meta.get("listing_url")
        page = re.findall(r"=(\d+)", page)
        page = ''.join(page)
        if page == '':
            page = 1

        category = response.css('.breadcrumb li a span::text').getall()
        category = ' > '.join(category)

        yield {
            "whiskey_name": response.css(".col-lg-6 h1::text").get(),
            "price": response.css(".current-price .price::text")
            .get("")
            .replace("₴", "")
            .strip(),
            "strength": response.css(
                'div[itemprop="description"] p:contains("Strength")::text'
            )
            .get("")
            .replace("Strength:", "")
            .replace("barrel", "")
            .replace("barreled", "")
            .strip(),
            "bottle_size": response.css(
                'div[itemprop="description"] p:contains("Bottle size")::text'
            )
            .get("")
            .replace("Bottle size:", "")
            .strip(),
            "page": page,
            "category": category,
            "listing_url": response.meta.get("listing_url"),
            "data_sheet": self.extract_alcohol_details(response),
            "url": response.url,
        }

    def extract_alcohol_details(self, response):

        alcohol_info = {}

        for alcohol_feature in response.css(".name"):
            alcohol_heading = alcohol_feature.css("::text").get()
            alcohol_value = alcohol_feature.css("dt+dd::text").get()
            alcohol_info[alcohol_heading] = alcohol_value

        return alcohol_info
