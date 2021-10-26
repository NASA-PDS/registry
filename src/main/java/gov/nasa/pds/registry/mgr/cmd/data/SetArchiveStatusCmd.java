package gov.nasa.pds.registry.mgr.cmd.data;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import org.apache.commons.cli.CommandLine;
import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import com.google.gson.Gson;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.RegistryRequestBuilder;
import gov.nasa.pds.registry.mgr.util.CloseUtils;


/**
 * A CLI command to set PDS label archive status in Elasticsearch registry index.
 * Status can be updated by LidVid or PackageId.
 * 
 * @author karpenko
 */
public class SetArchiveStatusCmd implements CliCommand
{
    private Set<String> statusNames; 
    private String filterMessage;

    /**
     * Constructor
     */
    public SetArchiveStatusCmd()
    {
        statusNames = new TreeSet<>();

        statusNames.add("ARCHIVED");
        statusNames.add("ARCHIVED_ACCUMULATING");
        statusNames.add("IN_LIEN_RESOLUTION");
        statusNames.add("IN_LIEN_RESOLUTION_ACCUMULATING");
        statusNames.add("IN_PEER_REVIEW");
        statusNames.add("IN_PEER_REVIEW_ACCUMULATING");
        statusNames.add("IN_QUEUE");
        statusNames.add("IN_QUEUE_ACCUMULATING");
        statusNames.add("LOCALLY_ARCHIVED");
        statusNames.add("LOCALLY_ARCHIVED_ACCUMULATING");
        statusNames.add("PRE_PEER_REVIEW");
        statusNames.add("PRE_PEER_REVIEW_ACCUMULATING");
        statusNames.add("SAFED");
        statusNames.add("STAGED");
        statusNames.add("SUPERSEDED");
    }
    
    
    @Override
    public void run(CommandLine cmdLine) throws Exception
    {
        if(cmdLine.hasOption("help"))
        {
            printHelp();
            return;
        }

        String esUrl = cmdLine.getOptionValue("es", "http://localhost:9200");
        String indexName = cmdLine.getOptionValue("index", Constants.DEFAULT_REGISTRY_INDEX);
        String authPath = cmdLine.getOptionValue("auth");
        
        String status = getStatus(cmdLine);
        
        String query = buildEsQuery(cmdLine, status);
        if(query == null)
        {
            throw new Exception("One of the following options is required: -lidvid, -packageId");
        }

        System.out.println("Elasticsearch URL: " + esUrl);
        System.out.println("            Index: " + indexName);
        System.out.println("       New status: " + status);
        System.out.println(filterMessage);
        System.out.println();

        RestClient client = null;
        
        try
        {
            // Create Elasticsearch client
            client = EsClientFactory.createRestClient(esUrl, authPath);

            // Create request
            Request req = new Request("POST", "/" + indexName + "/_update_by_query");
            req.setJsonEntity(query);
            
            // Execute request
            Response resp = client.performRequest(req);
            double numDeleted = extractNumUpdated(resp); 
            
            System.out.format("Updated %.0f document(s)\n", numDeleted);
        }
        catch(ResponseException ex)
        {
            throw new Exception(EsUtils.extractErrorMessage(ex));
        }
        finally
        {
            CloseUtils.close(client);
        }
    }

    
    /**
     * Extract number of updated records from Elasticsearch API response.
     * @param resp
     * @return number of updated records
     */
    @SuppressWarnings("rawtypes")
    private double extractNumUpdated(Response resp)
    {
        try
        {
            InputStream is = resp.getEntity().getContent();
            Reader rd = new InputStreamReader(is);
            
            Gson gson = new Gson();
            Object obj = gson.fromJson(rd, Object.class);
            rd.close();
            
            obj = ((Map)obj).get("updated");
            return (Double)obj;
        }
        catch(Exception ex)
        {
            return 0;
        }
    }

    
    /**
     * Create Elasticsearch query to update PDS label status
     * @param cmdLine
     * @param status
     * @return
     * @throws Exception
     */
    private String buildEsQuery(CommandLine cmdLine, String status) throws Exception
    {
        String id = cmdLine.getOptionValue("lidvid");
        if(id != null)
        {
            filterMessage = "           LIDVID: " + id;
            RegistryRequestBuilder bld = new RegistryRequestBuilder();
            return bld.createUpdateStatusRequest(status, "lidvid", id);
        }
        
        id = cmdLine.getOptionValue("packageId");
        if(id != null)
        {
            filterMessage = "       Package ID: " + id;
            RegistryRequestBuilder bld = new RegistryRequestBuilder();
            return bld.createUpdateStatusRequest(status, "_package_id", id);
        }

        return null;
    }

    
    /**
     * Get value of "-status" command-line parameter. 
     * Throw exception if invalid status is passed.
     * @param cmdLine
     * @return valid status value
     * @throws Exception Throw exception if invalid status is passed.
     */
    private String getStatus(CommandLine cmdLine) throws Exception
    {
        String tmp = cmdLine.getOptionValue("status");
        if(tmp == null) 
        {
            throw new Exception("Missing required parameter '-status'");
        }

        String status = tmp.toUpperCase();
        if(!statusNames.contains(status))
        {
            throw new Exception("Invalid '-status' parameter value: '" + tmp + "'");
        }
        
        return status;
    }
    
    
    /**
     * Print help screen
     */
    public void printHelp()
    {
        System.out.println("Usage: registry-manager set-archive-status <options>");

        System.out.println();
        System.out.println("Set product archive status");
        System.out.println();
        System.out.println("Required parameters:");
        System.out.println("  -status <status>   One of the following values:");

        for(String name: statusNames)
        {
            System.out.println("     " + name);
        }
        
        System.out.println("  -lidvid <id>       Update archive status of a document with given lidvid, or");
        System.out.println("  -packageId <id>    Update archive status of all documents with given package id"); 
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>       Authentication config file");
        System.out.println("  -es <url>          Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>      Elasticsearch index name. Default is 'registry'");
        System.out.println();
    }

}
