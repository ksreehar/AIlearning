import io, json, oci
from fdk import response

def handler(ctx, data: io.BytesIO = None):
    # Initialize Resource Principal Signer and Clients
    signer = oci.auth.signers.get_resource_principals_signer()
    obj_client = oci.object_storage.ObjectStorageClient({}, signer=signer)
    genai_client = oci.generative_ai_agent.GenerativeAiAgentClient({}, signer=signer)

    try:
        # 1. Parse Event Payload from Object Storage
        body = json.loads(data.getvalue())
        obj_name = body["data"]["resourceName"]
        bucket = body["data"]["additionalDetails"]["bucketName"]
        ns = body["data"]["additionalDetails"]["namespace"]

        if not obj_name.endswith(".html"):
            return response.Response(ctx, response_data="Skipping non-HTML file.")

        # 2. Logic: Detect Report Type & Snapshot ID (e.g., ADDM_PROD_500.html)
        rtype = "AWR" # Default
        if "ADDM" in obj_name.upper(): rtype = "ADDM"
        elif "ASH" in obj_name.upper(): rtype = "ASH"
        
        snap_id = obj_name.split('_')[-1].replace('.html', '')

        # 3. Create Metadata JSON Sidecar
        metadata = {
            "metadataAttributes": [
                {"name": "snapshot_id", "type": "integer", "value": int(snap_id)},
                {"name": "report_type", "type": "string", "value": rtype}
            ]
        }
        obj_client.put_object(ns, bucket, f"{obj_name}.json", json.dumps(metadata))

        # 4. Trigger Ingestion (Replace IDs with your actual OCIDs)
        ingest_details = oci.generative_ai_agent.models.CreateDataIngestionJobDetails(
            compartment_id="[COMPARTMENT_OCID]",
            data_source_id="[KNOWLEDGE_BASE_DATA_SOURCE_OCID]",
            display_name=f"AutoSync_{rtype}_{snap_id}"
        )
        genai_client.create_data_ingestion_job(ingest_details)

        return response.Response(ctx, response_data="Metadata created & Sync triggered.")
    except Exception as e:
        return response.Response(ctx, response_data=f"Error: {str(e)}")
