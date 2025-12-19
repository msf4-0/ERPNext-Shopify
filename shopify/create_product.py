import requests
import frappe
import json
from requests.auth import HTTPBasicAuth

@frappe.whitelist()
def create_shopify_product(itemCode, itemName, itemStatus, itemDescription, price, unitWeight, inventoryNum, imagePath,shopify_url, api_key, secret_key):
    # Construct the API payload without the image
    payload = {
        "product": {
            "title": itemName,
            "body_html": itemDescription,
            "vendor": "TD Furniture",
            "status": itemStatus,
            "variants": [
                {
                    "price": price,
                    "sku": itemCode,
                    "weight": unitWeight,
                    "inventory_management": "shopify",
                    "weight_unit": "kg",
                    "inventory_quantity": inventoryNum,
                    "old_inventory_quantity": inventoryNum,
                }
            ]
        }
    }

    
    headers = {"Content-Type": "application/json"}
    # Create product
    response = requests.post(
        shopify_url + "products.json",
        data=json.dumps(payload),
        headers=headers,
        auth=HTTPBasicAuth(api_key, secret_key)
    )

    if response.status_code == 201:
        frappe.msgprint(f"Product '{itemName}' created in Shopify.")
        

        product_data = response.json()
        product_id = product_data["product"]["id"]
        
        # Update the product to add the image
        image_upload_endpoint = f"{shopify_url}products/{product_id}.json"
        
        image_payload = {
            "product": {
                "id": product_id,
                "images": [{"src": imagePath}]
            }
        }
        
        image_payload_json = json.dumps(image_payload)
        image_response = requests.put(image_upload_endpoint, data=image_payload_json, headers=headers, auth=HTTPBasicAuth(api_key, secret_key))

        if image_response.status_code == 200:
            frappe.msgprint(f"Image added to the product '{itemName}' in Shopify.")
        else:
            frappe.msgprint(f"Failed to add the image to the product in Shopify. Error: {image_response.content}")

    else:
        frappe.msgprint(f"Failed to create the product in Shopify. Error: {response.content}")
    
    return product_id

# Attach the custom function to the 'Item' doctype's on_submit event
def after_insert(doc, method):
    # Fetch Shopify Access credentials
    shopify_doc = frappe.get_doc(
        "Shopify Access",
        frappe.get_value("Shopify Access", {}, "name")  # first Shopify Access record
    )

    if doc.shopify_product_id:
        return

    shopify_url = shopify_doc.shopify_url
    api_key = shopify_doc.api_key
    secret_key = shopify_doc.access_token

    # Determine Shopify status
    if doc.disabled:
        status = "archived"
    elif not doc.show_in_website:
        status = "draft"
    else:
        status = "active"

    # Push product
    product_id = create_shopify_product(
        doc.item_code,
        doc.item_name,
        status,
        doc.description,
        doc.standard_rate,
        doc.weight_per_unit,
        doc.opening_stock,
        doc.image,
        shopify_url,
        api_key,
        secret_key
    )
    if product_id:
        doc.db_set("shopify_product_id", str(product_id))

