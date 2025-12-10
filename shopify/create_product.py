import requests
import frappe
import json

@frappe.whitelist()
def create_shopify_product(itemCode, itemName, itemStatus, itemDescription, price, unitWeight, inventoryNum, shopify_url, imagePath):
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

    payload_json = json.dumps(payload)

    endpoint = 'products.json'
    # Shopify API headers and endpoint
    # Get credentials from Shopify Access
    shopify_access_list = frappe.get_all('Shopify Access', filters={'shopify_account': 'Main'}, fields=['name'])
    if not shopify_access_list:
        frappe.msgprint("No Shopify Access record found.", alert=True)
        return
    
    shopify_access = frappe.get_doc("Shopify Access", shopify_access_list[0]["name"])
    api_key = shopify_access.api_key
    api_token = shopify_access.access_token
    
    import base64
    auth_string = f"{api_key}:{api_token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_b64}"
    }
    final_url = shopify_url + endpoint

    # Send the POST request to create the product without the image
    response = requests.post(final_url, data=payload_json, headers=headers)

    if response.status_code == 201:
        frappe.msgprint(f"Product '{itemName}' created in Shopify.")

        product_data = response.json()
        product_id = product_data["product"]["id"]
        
        # Update the product to add the image
        image_upload_endpoint = f'products/{product_id}.json'
        image_upload_url = shopify_url + image_upload_endpoint
        image_payload = {
            "product": {
                "id": product_id,
                "images": [{"src": imagePath}]
            }
        }
        
        image_payload_json = json.dumps(image_payload)
        image_response = requests.put(image_upload_url, data=image_payload_json, headers=headers)

        if image_response.status_code == 200:
            frappe.msgprint(f"Image added to the product '{itemName}' in Shopify.")
        else:
            frappe.msgprint(f"Failed to add the image to the product in Shopify. Error: {image_response.content}")

    else:
        frappe.msgprint(f"Failed to create the product in Shopify. Error: {response.content}")

# Attach the custom function to the 'Item' doctype's on_submit event
def on_submit(doc, method):
    try:
        # Get Shopify Access record with Main account
        shopify_access_list = frappe.get_all('Shopify Access', filters={'shopify_account': 'Main'}, fields=['name'])
        
        if not shopify_access_list:
            frappe.msgprint("No Shopify Access record found. Please configure Shopify Access first.", alert=True)
            return
        
        shopify_access = frappe.get_doc("Shopify Access", shopify_access_list[0]["name"])
        
        if not shopify_access.shopify_url:
            frappe.msgprint("Shopify URL is not configured in Shopify Access record.", alert=True)
            return
        
        # Get item details with defaults for missing fields
        item_code = doc.item_code or ""
        item_name = doc.item_name or doc.item_code or "Untitled Product"
        item_status = getattr(doc, 'prod_status', 'active') or 'active'
        item_description = doc.description or ""
        price = doc.standard_rate or 0
        unit_weight = getattr(doc, 'weight_per_unit', 0) or 0
        inventory_num = getattr(doc, 'opening_stock', 0) or 0
        image_path = getattr(doc, 'image', '') or ''
        
        # Create product in Shopify
        create_shopify_product(
            item_code, 
            item_name, 
            item_status, 
            item_description, 
            str(price), 
            str(unit_weight), 
            int(inventory_num), 
            shopify_access.shopify_url, 
            image_path
        )
    except Exception as e:
        frappe.log_error(f"Error creating product in Shopify: {str(e)}", "Shopify Create Product Error")
        frappe.msgprint(f"Error creating product in Shopify: {str(e)}", alert=True)

# Ensure the on_submit function is triggered when an 'Item' document is submitted
frappe.get_doc('DocType', 'Item').on_submit = on_submit
