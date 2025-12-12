import frappe

@frappe.whitelist()
def sync_all(api_key, access_token, shopify_url):

    from shopify.retrieve_product import retrieve_shopify_products
    from shopify.retrieve_customer import retrieve_shopify_customers
    from shopify.retrieve_order import retrieve_shopify_orders

    retrieve_shopify_products(api_key, access_token, shopify_url)
    retrieve_shopify_customers(api_key, access_token, shopify_url)
    retrieve_shopify_orders(api_key, access_token, shopify_url)

    return "OK"
