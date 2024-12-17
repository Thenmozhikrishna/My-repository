from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from xml.etree.ElementTree import Element, tostring
from pydantic import BaseModel
from typing import List, Union
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring


app = FastAPI()

TALLY_URL = "http://127.0.0.1:9000/"
# TALLY_URL = "http://60.60.60.43:9000/"
# TALLY_URL = "http://192.168.15.99:9000/"

class LedgerEntry(BaseModel):
    ledger_name: str
    is_deemed_positive: bool
    amount: float

class Voucher(BaseModel):
    date: str
    vch_status_date: str
    reference_date: str
    narration: str
    voucher_type_name: str
    voucher_number: str
    reference: str
    ledger_entries: List[LedgerEntry]

def dict_to_xml(tag, d):
    """Turn a simple dict of key/value pairs into XML"""
    elem = Element(tag)
    if isinstance(d, dict):
        for key, val in d.items():
            child = Element(key)
            child.text = str(val)
            elem.append(child)
    else:
        elem.text = str(d)
    return elem

class InventoryEntry(BaseModel):
    stock_item_name: str
    hsn_item_source: str
    rate: str
    amount: str
    actual_qty: str
    billed_qty: str
    order_no: str
    tracking_number: str
    order_due_date: str
    is_deemed_positive: str = "Yes"  

class Invoice(BaseModel):
    voucher_type: str
    date: str
    reference_date: str
    voucher_number: str
    basic_terms_of_supply: str
    order_no: str
    tracking_number: str
    order_due_date: str
    party_name: str
    narration: str = "Tested for invoice"  
    party_ledger_name: str
    basic_buyer_name: str
    consignee_emailing_name: str
    is_deemed_positive: str = "Yes"
    inventory_entries: list[InventoryEntry] 


# added for divas testing


class VoucherEntry(BaseModel):
    company_name: str
    voucher_type: str
    date: str
    reference_date: str
    voucher_status_date: str
    narration: str
    object_update_action: str
    voucher_type_name: str
    voucher_number: str
    reference: str
    persisted_view: str
    voucher_status_voucher_type: str
    effective_date: str
    debit_ledger_name: str
    debit_amount: float
    debit_narration: str
    debit_category: str
    debit_cost_centre: str
    credit_ledger_name: str
    credit_amount: float
    credit_narration: str

@app.post("/voucher_entry/")
async def voucher_entry(data: VoucherEntry):
    # XML structure
    envelope = Element('ENVELOPE')

    header = SubElement(envelope, 'HEADER')
    tally_request = SubElement(header, 'TALLYREQUEST')
    tally_request.text = 'Import Data'

    body = SubElement(envelope, 'BODY')
    import_data = SubElement(body, 'IMPORTDATA')

    request_desc = SubElement(import_data, 'REQUESTDESC')
    report_name = SubElement(request_desc, 'REPORTNAME')
    report_name.text = 'Vouchers'

    static_variables = SubElement(request_desc, 'STATICVARIABLES')
    current_company = SubElement(static_variables, 'SVCURRENTCOMPANY')
    current_company.text = data.company_name

    request_data = SubElement(import_data, 'REQUESTDATA')
    tally_message = SubElement(request_data, 'TALLYMESSAGE', attrib={'xmlns:UDF': 'TallyUDF'})

    voucher = SubElement(tally_message, 'VOUCHER', attrib={
        'VCHTYPE': data.voucher_type,
        'ACTION': 'Create',
        'OBJVIEW': 'Accounting Voucher View'
    })

    # Voucher fields
    SubElement(voucher, 'DATE').text = data.date
    SubElement(voucher, 'REFERENCEDATE').text = data.reference_date
    SubElement(voucher, 'VCHSTATUSDATE').text = data.voucher_status_date
    SubElement(voucher, 'NARRATION').text = data.narration
    SubElement(voucher, 'OBJECTUPDATEACTION').text = data.object_update_action
    SubElement(voucher, 'VOUCHERTYPENAME').text = data.voucher_type_name
    SubElement(voucher, 'VOUCHERNUMBER').text = data.voucher_number
    SubElement(voucher, 'REFERENCE').text = data.reference
    SubElement(voucher, 'PERSISTEDVIEW').text = data.persisted_view
    SubElement(voucher, 'VCHSTATUSVOUCHERTYPE').text = data.voucher_status_voucher_type
    SubElement(voucher, 'EFFECTIVEDATE').text = data.effective_date

    # Debit Ledger Entry
    ledger_entry_debit = SubElement(voucher, 'ALLLEDGERENTRIES.LIST')
    SubElement(ledger_entry_debit, 'NARRATION').text = data.debit_narration
    SubElement(ledger_entry_debit, 'LEDGERNAME').text = data.debit_ledger_name
    SubElement(ledger_entry_debit, 'ISDEEMEDPOSITIVE').text = 'Yes'
    SubElement(ledger_entry_debit, 'ISLASTDEEMEDPOSITIVE').text = 'Yes'
    SubElement(ledger_entry_debit, 'AMOUNT').text = f"-{data.debit_amount:.2f}"
    SubElement(ledger_entry_debit, 'VATEXPAMOUNT').text = f"-{data.debit_amount:.2f}"

    category_allocation = SubElement(ledger_entry_debit, 'CATEGORYALLOCATIONS.LIST')
    SubElement(category_allocation, 'CATEGORY').text = data.debit_category
    SubElement(category_allocation, 'ISDEEMEDPOSITIVE').text = 'Yes'

    cost_centre_allocation = SubElement(category_allocation, 'COSTCENTREALLOCATIONS.LIST')
    SubElement(cost_centre_allocation, 'NAME').text = data.debit_cost_centre
    SubElement(cost_centre_allocation, 'AMOUNT').text = f"-{data.debit_amount:.2f}"

    # Credit Ledger Entry
    ledger_entry_credit = SubElement(voucher, 'ALLLEDGERENTRIES.LIST')
    SubElement(ledger_entry_credit, 'NARRATION').text = data.credit_narration
    SubElement(ledger_entry_credit, 'LEDGERNAME').text = data.credit_ledger_name
    SubElement(ledger_entry_credit, 'ISDEEMEDPOSITIVE').text = 'No'
    SubElement(ledger_entry_credit, 'ISLASTDEEMEDPOSITIVE').text = 'No'
    SubElement(ledger_entry_credit, 'AMOUNT').text = f"{data.credit_amount:.2f}"
    SubElement(ledger_entry_credit, 'VATEXPAMOUNT').text = f"{data.credit_amount:.2f}"

    # Convert XML tree to string
    xml_data = tostring(envelope).decode()

    print(xml_data)

    headers = {"Content-Type": "application/xml"}

    try:
        response = requests.post(TALLY_URL, data=xml_data, headers=headers)
        response.raise_for_status()
        
        if response.status_code == 200:
            # Parse the response to check for errors
            print('response.text:', response.text)

            try:
                # Parse the XML response
                root = ET.fromstring(response.text)
                
                # Convert XML to dictionary-like structure
                response_dict = {child.tag: child.text for child in root}

                # Check for exceptions or errors
                exceptions = response_dict.get('EXCEPTIONS', '0')
                errors = response_dict.get('ERRORS', '0')

                if exceptions == '1' or errors != '0':
                    # If an error or exception is found, raise an HTTPException with a 400 status code
                    raise HTTPException(status_code=400, detail={
                        "message": "Error in Tally",
                        "error_details": response_dict
                    })

                # No errors, return success
                return {"message": "Journal posted successfully", "response_details": response_dict}

            except ET.ParseError:
                raise HTTPException(status_code=500, detail="Failed to parse XML response")

        return {"status": "success", "response": response.text}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error sending data to Tally: {e}")


# added for divas testing ends here





inventory_entry_template = '''

<ALLINVENTORYENTRIES.LIST>
       <STOCKITEMNAME>{stock_item_name}</STOCKITEMNAME>
       <GSTSOURCETYPE>Stock Item</GSTSOURCETYPE>
       <GSTITEMSOURCE>{stock_item_name}</GSTITEMSOURCE>
       <HSNSOURCETYPE>Stock Item</HSNSOURCETYPE>
       <HSNITEMSOURCE>{hsn_item_source}</HSNITEMSOURCE>
       <ISDEEMEDPOSITIVE>{is_deemed_positive}</ISDEEMEDPOSITIVE>
       <RATE>{rate}</RATE>
       <AMOUNT>-{amount}</AMOUNT>
       <ACTUALQTY>{actual_qty}</ACTUALQTY>
       <BILLEDQTY>{billed_qty}</BILLEDQTY>
       <BATCHALLOCATIONS.LIST>
        <GODOWNNAME>Admin</GODOWNNAME>
        <BATCHNAME>Primary Batch</BATCHNAME>
        <DESTINATIONGODOWNNAME>Admin</DESTINATIONGODOWNNAME>
        <ORDERNO>{order_no}</ORDERNO>
        <TRACKINGNUMBER>{tracking_number}</TRACKINGNUMBER>
        <DYNAMICCSTISCLEARED>No</DYNAMICCSTISCLEARED>
        <AMOUNT>-{amount}</AMOUNT>
        <ACTUALQTY>{actual_qty}</ACTUALQTY>
        <BILLEDQTY>{billed_qty}</BILLEDQTY>
        <ORDERDUEDATE  P="{order_due_date}">{order_due_date}</ORDERDUEDATE>
       </BATCHALLOCATIONS.LIST>
       <ACCOUNTINGALLOCATIONS.LIST>
        <LEDGERNAME>Raw Material</LEDGERNAME>
        <ISDEEMEDPOSITIVE>{is_deemed_positive}</ISDEEMEDPOSITIVE>
        <ISLASTDEEMEDPOSITIVE>Yes</ISLASTDEEMEDPOSITIVE>
        <AMOUNT>-{amount}</AMOUNT>
       </ACCOUNTINGALLOCATIONS.LIST>
      </ALLINVENTORYENTRIES.LIST>

'''


invoice_format = '''
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
 <BODY>
  <IMPORTDATA>
   <REQUESTDESC>
    <REPORTNAME>Vouchers</REPORTNAME>
    <STATICVARIABLES>
     <SVCURRENTCOMPANY>{svc_current_company}</SVCURRENTCOMPANY>
    </STATICVARIABLES>
   </REQUESTDESC>
   <REQUESTDATA>
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER VCHTYPE="{voucher_type}" ACTION="Create" OBJVIEW="Invoice Voucher View">
     <NARRATION>{narration}</NARRATION>
      <DATE>{date}</DATE>
      <REFERENCEDATE>{reference_date}</REFERENCEDATE>
      <VCHSTATUSDATE>{date}</VCHSTATUSDATE>
      <PARTYNAME>{party_name}</PARTYNAME>
      <VOUCHERTYPENAME>{voucher_type}</VOUCHERTYPENAME>
      <PARTYLEDGERNAME>{party_ledger_name}</PARTYLEDGERNAME>
      <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
      <BASICBUYERNAME>{basic_buyer_name}</BASICBUYERNAME>
      <REFERENCE>265675677</REFERENCE>
      <CONSIGNEEMAILINGNAME>{consignee_emailing_name}</CONSIGNEEMAILINGNAME>
      <BASICBASEPARTYNAME>{party_name}</BASICBASEPARTYNAME>
      <PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>
      <VCHSTATUSVOUCHERTYPE>Purchase</VCHSTATUSVOUCHERTYPE>
      <VCHENTRYMODE>Item Invoice</VCHENTRYMODE>
      <DIFFACTUALQTY>Yes</DIFFACTUALQTY>
      <ISMSTFROMSYNC>No</ISMSTFROMSYNC>
      <ISDELETED>No</ISDELETED>
      <EFFECTIVEDATE>{date}</EFFECTIVEDATE>
      <BASICTERMSOFSUPPLY>{basic_terms_of_supply}</BASICTERMSOFSUPPLY>     
        {inventory_entries}
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>{party_ledger_name}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
       <AMOUNT>{amount}</AMOUNT>
      </LEDGERENTRIES.LIST>
	  </VOUCHER>
    </TALLYMESSAGE>
</REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>
'''



@app.post('/invoice_post')
async def invoice_post(voucher: Invoice):
    try:
        svc_current_company = "Avision Systems Pvt Ltd"
        
        inventory_entries_xml = ""
        total_amount = 0  # Initialize total amount if needed

        # Generate inventory entries XML
        for entry in voucher.inventory_entries:
            inventory_entries_xml += inventory_entry_template.format(
                stock_item_name=entry.stock_item_name,
                hsn_item_source=entry.hsn_item_source,
                rate=entry.rate,
                amount=entry.amount,
                actual_qty=entry.actual_qty,
                billed_qty=entry.billed_qty,
                order_no=entry.order_no,
                tracking_number=entry.tracking_number,
                order_due_date=entry.order_due_date,
                is_deemed_positive=entry.is_deemed_positive
            )
            # Summing up the amounts if needed
            total_amount += float(entry.amount)  # Assuming amounts are numeric

        # Format the main invoice XML
        formatted_invoice = invoice_format.format(
            svc_current_company=svc_current_company,
            voucher_type = voucher.voucher_type,
            date=voucher.date,
            reference_date=voucher.reference_date,
            voucher_number=voucher.voucher_number,
            basic_terms_of_supply=voucher.basic_terms_of_supply,
            party_name=voucher.party_name,
            narration=voucher.narration,
            party_ledger_name=voucher.party_ledger_name,
            basic_buyer_name=voucher.basic_buyer_name,
            consignee_emailing_name=voucher.consignee_emailing_name,
            inventory_entries=inventory_entries_xml,  # Inject the generated inventory entries
            amount=total_amount  # Use total amount if needed in the ledger
        )

        print('data_posted:', formatted_invoice)

        headers = {
            "Content-Type": "application/xml"
        }

        response = requests.post(TALLY_URL, data=formatted_invoice, headers=headers)

        # Check if Tally responded with an error
        response.raise_for_status()
        
        if response.status_code == 200:
            # Parse the response to check for errors
            print('response.text:', response.text)

            try:
                # Parse the XML response
                root = ET.fromstring(response.text)
                
                # Convert XML to dictionary-like structure
                response_dict = {child.tag: child.text for child in root}

                # Check for exceptions or errors
                exceptions = response_dict.get('EXCEPTIONS', '0')
                errors = response_dict.get('ERRORS', '0')

                if exceptions == '1' or errors != '0':
                    # If an error or exception is found, raise an HTTPException with a 400 status code
                    raise HTTPException(status_code=400, detail={
                        "message": "Error in Tally",
                        "error_details": response_dict
                    })

                # No errors, return success
                return {"message": "Invoice posted successfully", "response_details": response_dict}

            except ET.ParseError:
                raise HTTPException(status_code=500, detail="Failed to parse XML response")

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=f"HTTP error occurred: {http_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/post-voucher")
async def post_voucher(voucher: Voucher):
    try:
        # Construct the XML
        voucher_elem = Element("VOUCHER")
        voucher_elem.append(dict_to_xml("DATE", voucher.date))
        voucher_elem.append(dict_to_xml("VCHSTATUSDATE", voucher.vch_status_date))
        voucher_elem.append(dict_to_xml("REFERENCEDATE", voucher.reference_date))
        voucher_elem.append(dict_to_xml("NARRATION", voucher.narration))
        voucher_elem.append(dict_to_xml("VOUCHERTYPENAME", voucher.voucher_type_name))
        voucher_elem.append(dict_to_xml("VOUCHERNUMBER", voucher.voucher_number))
        voucher_elem.append(dict_to_xml("REFERENCE", voucher.reference))

        for entry in voucher.ledger_entries:
            entry_elem = Element("ALLLEDGERENTRIES.LIST")
            entry_elem.append(dict_to_xml("LEDGERNAME", entry.ledger_name))
            entry_elem.append(dict_to_xml("ISDEEMEDPOSITIVE", "Yes" if entry.is_deemed_positive else "No"))
            entry_elem.append(dict_to_xml("AMOUNT", entry.amount))
            voucher_elem.append(entry_elem)

        tally_message_elem = Element("TALLYMESSAGE")
        tally_message_elem.append(voucher_elem)

        data_elem = Element("DATA")
        data_elem.append(tally_message_elem)

        body_elem = Element("BODY")
        body_elem.append(Element("DESC"))
        body_elem.append(data_elem)

        header_elem = Element("HEADER")
        header_elem.append(dict_to_xml("VERSION", "1"))
        header_elem.append(dict_to_xml("TALLYREQUEST", "Import"))
        header_elem.append(dict_to_xml("TYPE", "Data"))
        header_elem.append(dict_to_xml("ID", "Vouchers"))

        envelope_elem = Element("ENVELOPE")
        envelope_elem.append(header_elem)
        envelope_elem.append(body_elem)

        xml_data = tostring(envelope_elem, encoding='unicode')

        headers = {
            "Content-Type": "application/xml"
        }

        response = requests.post(TALLY_URL, data=xml_data, headers=headers)

        # Check if Tally responded with an error
        response.raise_for_status()

        return JSONResponse(content={"message": "Voucher posted successfully", "status_code": response.status_code})

    except requests.RequestException as e:
        # Log the error and raise an HTTPException
        print(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail="Error posting voucher to Tally")

    except Exception as e:
        # Catch any other exceptions and return a generic error message
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

