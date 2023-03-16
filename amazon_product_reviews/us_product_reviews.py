import httpx

url = "https://www.amazon.com/hz/reviews-render/ajax/reviews/get/ref=cm_cr_arp_d_paging_btm_next_2"
client = httpx.Client(http2=True)
response = client.post(url, data={"pageNumber": 2, "reftag": "cm_cr_arp_d_paging_btm_next_2", "pageSize": 10,
                                      "asin": "B0BDDRPJCX", "scope": "reviewsAjax0"})

print(response.text)
