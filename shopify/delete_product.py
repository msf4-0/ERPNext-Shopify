import requests
import frappe
import json
from requests.auth import HTTPBasicAuth

@frappe.whitelist()
def delete_shopify_product(productID, shopify_url, secret_key):

    # Send the POST request to create the product
    
    headers = {
        "X-Shopify-Access-Token": secret_key,
        "Content-Type": "application/json"
    }

    response = requests.delete(
        f"{shopify_url}products/{productID}.json",
        headers=headers
    )

    if response.status_code == 200:
        frappe.msgprint(f"Product deleted from Shopify Account.")
    else:
        frappe.msgprint("Failed to delete the product in Shopify. Error: {response.content}")

# Attach the custom function to the 'Item' doctype's on_submit event
def on_submit(doc, method):
    shopify_doc = frappe.get_doc(
        "Shopify Access",
        frappe.get_value("Shopify Access", {}, "name")  # first Shopify Access record
    )

    shopify_url = shopify_doc.shopify_url
    secret_key = shopify_doc.access_token

    delete_shopify_product(doc.shopify_product_id, shopify_url, secret_key)

