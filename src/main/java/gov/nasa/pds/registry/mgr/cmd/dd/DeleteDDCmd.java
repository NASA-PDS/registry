package gov.nasa.pds.registry.mgr.cmd.dd;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.Map;

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
 * A CLI command to delete records from the data dictionary index in Elasticsearch.
 * Data can be deleted by ID, or namespace. All data can be also deleted.
 *  
 * @author karpenko
 */
public class DeleteDDCmd implements CliCommand
{
    private String filterMessage;

    /**
     * Constructor
     */
    public DeleteDDCmd()
    {
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

        String query = buildEsQuery(cmdLine);
        if(query == null)
        {
            throw new Exception("One of the following options is required: -id, -ns, -all");
        }

        System.out.println("Elasticsearch URL: " + esUrl);
        System.out.println("            Index: " + indexName);
        System.out.println(filterMessage);
        System.out.println();
        
        RestClient client = null;
        
        try
        {
            // Create Elasticsearch client
            client = EsClientFactory.createRestClient(esUrl, authPath);

            // Create request
            Request req = new Request("POST", "/" + indexName + "-dd" + "/_delete_by_query");
            req.setJsonEntity(query);
            
            // Execute request
            Response resp = client.performRequest(req);
            double numDeleted = extractNumDeleted(resp); 
            
            System.out.format("Deleted %.0f document(s)\n", numDeleted);
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
     * Extract number of deleted records from Elasticsearch delete API response.
     * @param resp
     * @return number of deleted records
     */
    @SuppressWarnings("rawtypes")
    private double extractNumDeleted(Response resp)
    {
        try
        {
            InputStream is = resp.getEntity().getContent();
            Reader rd = new InputStreamReader(is);
            
            Gson gson = new Gson();
            Object obj = gson.fromJson(rd, Object.class);
            rd.close();
            
            obj = ((Map)obj).get("deleted");
            return (Double)obj;
        }
        catch(Exception ex)
        {
            return 0;
        }
    }
    
    
    /**
     * Create Elasticsearch query to delete records from data dictionary index.
     * @param cmdLine
     * @return
     * @throws Exception
     */
    private String buildEsQuery(CommandLine cmdLine) throws Exception
    {
        RegistryRequestBuilder bld = new RegistryRequestBuilder();
        
        String id = cmdLine.getOptionValue("id");
        if(id != null)
        {
            filterMessage = "               ID: " + id;
            return bld.createFilterQuery("_id", id);
        }
        
        id = cmdLine.getOptionValue("ns");
        if(id != null)
        {
            filterMessage = "        Namespace: " + id;
            return bld.createFilterQuery("class_ns", id);
        }

        if(cmdLine.hasOption("all"))
        {
            filterMessage = "Delete all documents ";
            return bld.createMatchAllQuery();
        }

        return null;
    }
    
    
    /**
     * Print help screen
     */
    public void printHelp()
    {
        System.out.println("Usage: registry-manager delete-dd <options>");

        System.out.println();
        System.out.println("Delete data from data dictionary index");
        System.out.println();
        System.out.println("Required parameters, one of:");
        System.out.println("  -id <id>          Delete data by ID (Full field name)");
        System.out.println("  -ns <namespace>   Delete data by namespace");
        System.out.println("  -all              Delete all data");
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>      Authentication config file");
        System.out.println("  -es <url>         Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>     Elasticsearch index name. Default is 'registry'");
        System.out.println();
    }

}
