import requests
import frappe
import json
from requests.auth import HTTPBasicAuth

@frappe.whitelist()
def update_shopify_product(productID, itemCode, itemName, itemStatus, itemDescription, price, unitWeight, inventoryNum, shopify_url, access_token, imagePath):
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    payload = {
        "product": {
            "title": itemName,
            "body_html": itemDescription,
            "vendor": "TD Furniture",
            "status": itemStatus,
            "variants": [{
                "sku": itemCode,
                "price": price,
                "weight": unitWeight,
                "weight_unit": "kg",
                "inventory_management": "shopify",
                "inventory_quantity": inventoryNum
            }]
        }
    }

    # Update product
    response = requests.put(f"{shopify_url}products/{productID}.json", json=payload, headers=headers)
    
    if response.status_code == 200:
        frappe.msgprint(f"Product '{itemName}' updated in Shopify.")

        # Upload image
        image_upload_endpoint = f"{shopify_url}products/{productID}.json"
        
        image_payload = {
            "product": {
                "id": productID,
                "image": [{"src": imagePath}]
            }
        }
        
        image_payload_json = json.dumps(image_payload)
        image_response = requests.post(image_upload_endpoint, data=image_payload_json, headers=headers)

        if image_response.status_code == 201:
            frappe.msgprint(f"Image updated for product '{itemName}' in Shopify.")
        else:
            frappe.log_error(title="Shopify Image Upload Failed", message=image_response.text)
    else:
        frappe.log_error(title="Shopify Product Update Failed", message=response.text)
        frappe.msgprint(f"Failed to update product '{itemName}' in Shopify. Status: {response.status_code}")


# Attach the custom function to the 'Item' doctype's on_submit event
def on_submit(doc, method):
    shopify_doc = frappe.get_doc(
        "Shopify Access",
        frappe.get_value("Shopify Access", {}, "name")  # first Shopify Access record
    )
    
    # Determine Shopify status
    if doc.disabled:
        status = "archived"
    elif not doc.show_in_website:
        status = "draft"
    else:
        status = "active"

    update_shopify_product(doc.shopify_product_id, doc.item_code, doc.item_name, status, doc.description, doc.standard_rate, doc.weight_per_unit, doc.opening_stock, shopify_doc.shopify_url, shopify_doc.access_token, doc.image)


